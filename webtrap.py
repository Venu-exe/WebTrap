import http.server
import socketserver
import logging
import urllib.parse
import os
import json
import re
import time
import sys
import smtplib
import threading
from email.mime.text import MIMEText
from datetime import datetime

# Configuration
PORT = 8080
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "honeypot.log")
HTML_DIR = "html"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Threat Signatures (Deep Packet Inspection)
SIGNATURES = {
    "SQL_INJECTION": re.compile(r"(%27)|(')|(--)|(%23)|(#)|(UNION)|(SELECT)|(SLEEP)", re.IGNORECASE),
    "XSS_SCRIPTING": re.compile(r"(<script>)|(%3Cscript%3E)|(javascript:)|(onerror=)|(alert\()", re.IGNORECASE),
    "CMD_INJECTION": re.compile(r"(%3B)|(;)|(\|)|(`)|(\$\()|(whoami)|(cat\s+/etc/passwd)", re.IGNORECASE),
    "PATH_TRAVERSAL": re.compile(r"(\.\./)|(%2e%2e%2f)", re.IGNORECASE)
}

# Email Alert Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("WEBTRAP_SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("WEBTRAP_SENDER_PASSWORD", "")  # Gmail App Password, not your real password
RECEIVER_EMAIL = os.environ.get("WEBTRAP_RECEIVER_EMAIL", "")
ALERT_COOLDOWN_SECONDS = 300  # don't re-alert on the same IP within 5 minutes

_last_alert_time = {}  # tracks cooldown per IP
_alert_lock = threading.Lock()


def send_email_alert(ip, attack_type, tags, details):
    if not (SENDER_EMAIL and SENDER_PASSWORD and RECEIVER_EMAIL):
        return  # alerts not configured, skip silently

    with _alert_lock:
        last_time = _last_alert_time.get(ip, 0)
        if time.time() - last_time < ALERT_COOLDOWN_SECONDS:
            return  # still in cooldown, skip
        _last_alert_time[ip] = time.time()

    def _send():
        try:
            subject = f"[WebTrap ALERT] {attack_type} from {ip}"
            body = (
                f"WebTrap detected a malicious request.\n\n"
                f"Attacker IP: {ip}\n"
                f"Attack Type: {attack_type}\n"
                f"Signatures: {', '.join(tags)}\n"
                f"Details: {details}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = SENDER_EMAIL
            msg["To"] = RECEIVER_EMAIL

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            print(f"[*] Email alert sent for {ip}")
        except Exception as e:
            print(f"[ERROR] Failed to send email alert: {str(e)}")

    threading.Thread(target=_send, daemon=True).start()


class AdvancedHoneypotHandler(http.server.BaseHTTPRequestHandler):
    
    def analyze_payload(self, payload_str):
        threat_tags = []
        for threat_type, regex in SIGNATURES.items():
            if regex.search(payload_str):
                threat_tags.append(threat_type)
        return threat_tags

    def log_attack(self, attack_type, details, tags):
        client_ip = self.client_address[0]
        tag_str = ",".join(tags) if tags else "GENERIC"
        
        log_entry = f"IP:{client_ip} | METHOD:{self.command} | PATH:{self.path} | TYPE:{attack_type} | TAGS:[{tag_str}] | DETAILS:{details}"
        
        print(f"[!] {log_entry}")
        logging.info(log_entry)

        # Only alert on real threats, not routine reconnaissance
        if attack_type in ("MALICIOUS_GET", "MALICIOUS_POST"):
            send_email_alert(client_ip, attack_type, tags, details)

        return tag_str

    def apply_tarpit(self):
        print(f"[*] Engaging Tarpit Defense for {self.client_address[0]}")
        time.sleep(5) 

    def serve_fake_login(self):
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Server", "nginx/1.18.0 (Ubuntu)")
            self.end_headers()
            
            with open(os.path.join(HTML_DIR, "index.html"), "rb") as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.wfile.write(b"<html><body><h1>Authentication Required</h1><form method='POST'><input name='username'><input type='password' name='password'><input type='submit'></form></body></html>")
        except Exception as e:
            print(f"[ERROR] Failed to serve HTML: {str(e)}")

    def do_GET(self):
        try:
            tags = self.analyze_payload(self.path)
            if tags:
                self.log_attack("MALICIOUS_GET", "Path Traversal/Payload Detected", tags)
                self.apply_tarpit()
            else:
                self.log_attack("RECONNAISSANCE", "Visited entry page", ["SCAN"])
                
            self.serve_fake_login()
        except Exception as e:
            print(f"[ERROR] GET Request processing failed: {str(e)}")

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            parsed_data = urllib.parse.parse_qs(post_data)
            
            # Extract precise credentials if present
            username = parsed_data.get('username', [''])[0]
            password = parsed_data.get('password', [''])[0]
            
            if username or password:
                creds = f"username={username}, password={password}"
            else:
                creds = json.dumps(parsed_data)
            
            tags = self.analyze_payload(post_data)
            
            if tags:
                self.log_attack("MALICIOUS_POST", f"Payload: {creds}", tags)
                self.apply_tarpit()
            else:
                self.log_attack("CREDENTIAL_STUFFING", f"Attempt: {creds}", ["BRUTEFORCE"])
                
            self.send_response(302)
            self.send_header("Location", "/?error=invalid_credentials")
            self.end_headers()
        except Exception as e:
            print(f"[ERROR] POST Request processing failed: {str(e)}")

if __name__ == "__main__":
    print(f"[*] Starting WebTrap Honeypot Service on port {PORT}...")
    print(f"[*] Tarpit Active Defense Engine: ENABLED")
    print(f"[*] Deep Packet Inspection: ENABLED")
    print(f"[*] Awaiting network traffic...")
    
    try:
        with socketserver.TCPServer(("", PORT), AdvancedHoneypotHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Terminating WebTrap Service.")
        sys.exit(0)