import http.server
import socketserver
import logging
import urllib.parse
import os
import json
import re
import time
import sys
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
