# Final Year Project Report: WebTrap (Active Web-Based Honeypot & Threat Profiler)

---

## 1. Abstract
As cyber threats become increasingly automated, traditional passive defense mechanisms like static firewalls are often insufficient, leading to "alert fatigue" and a lack of actionable threat intelligence. This project proposes **WebTrap**, an active defense honeypot and threat intelligence profiler. Built using Python and Bash, WebTrap simulates a vulnerable enterprise gateway to lure automated scanners and malicious actors. Upon interaction, it utilizes Deep Packet Inspection (DPI) to categorize the attack (e.g., SQL Injection, XSS) and employs "Tarpitting" to degrade the attacker's resources. Concurrently, an asynchronous Bash-based profiler extracts the attacker's IP, conducts OSINT gathering for geolocation and ISP tracing, and generates a dynamic HTML threat report. The system successfully demonstrates how deception technology can shift network security from a reactive posture to a proactive one.

---

## 2. Introduction
### 2.1 Background
The proliferation of automated exploitation tools and botnets has fundamentally changed the cybersecurity landscape. Organizations are bombarded with thousands of malicious requests per minute. Traditional Intrusion Detection Systems (IDS) and firewalls generate excessive logs, providing minimal context about the attacker's motives, location, or infrastructure.

### 2.2 Problem Statement
How can an organization actively gather intelligence on attackers, slow down automated network scanning, and automatically classify threat payloads without exposing real infrastructure to risk?

### 2.3 Proposed Solution
**WebTrap** is designed to address this problem by employing Deception Technology. By deploying a simulated web portal that appears vulnerable, organizations can safely intercept attackers. Instead of immediately dropping the malicious connection, the system wastes the attacker's time and profiles their physical location, generating a high-fidelity intelligence report.

---

## 3. Literature Review & Existing Systems
### 3.1 Passive Firewalls vs. Active Defense
Traditional firewalls (like `iptables` or hardware firewalls) operate on a binary 'allow/block' principle. While effective at stopping known bad traffic, they do not punish the attacker. Active defense concepts, such as honeypots (e.g., Cowrie, Dionaea), invite the attack to study the methodology. WebTrap innovates on standard honeypots by implementing active retaliation through network "Tarpitting."

### 3.2 Tarpitting Techniques
A "Tarpit" is a defensive mechanism that delays incoming connections. By slowing down the HTTP response, automated tools like `Nmap`, `DirBuster`, or `SQLmap` are forced to keep their TCP threads open, significantly degrading their performance and wasting the attacker's computing resources.

---

## 4. System Architecture
### 4.1 High-Level Design
The WebTrap framework is decoupled into two primary micro-engines to ensure stability and separation of concerns:
1. **The Lure Engine (Python 3):** Handles network sockets, serves the HTML decoy, and performs payload inspection.
2. **The Profiling Engine (Bash):** Monitors the file system for log changes, interacts with external OSINT APIs, and writes HTML reports.

### 4.2 Data Flow Diagram
1. Attacker sends HTTP Request (e.g., `POST /auth`).
2. Python Server receives request -> Analyzes Payload using Regex Engine.
3. If payload is malicious -> Trigger Tarpit (Wait 5 seconds) -> Log exact threat signature.
4. Bash Profiler detects new log entry -> Extracts IP Address.
5. Bash Profiler queries `ipinfo.io` -> Retrieves Geolocation & ASN.
6. Bash Profiler writes data to `threat_report.html`.

---

## 5. Methodology & Implementation

### 5.1 Deep Packet Inspection (DPI) Module
The Python engine utilizes pre-defined Regular Expressions to classify incoming payloads. 
```python
# Example Threat Signatures used in WebTrap
SIGNATURES = {
    "SQL_INJECTION": re.compile(r"(%27)|(')|(--)|(%23)|(#)|(UNION)|(SELECT)", re.IGNORECASE),
    "XSS_SCRIPTING": re.compile(r"(<script>)|(%3Cscript%3E)|(javascript:)", re.IGNORECASE),
    "PATH_TRAVERSAL": re.compile(r"(\.\./)|(%2e%2e%2f)", re.IGNORECASE)
}
```
If a payload matches any of these signatures, it is tagged (e.g., `[XSS_SCRIPTING]`) and passed to the logging module.

### 5.2 The Tarpit Engine
When a malicious payload is confirmed by the DPI module, the system invokes the Tarpit defense:
```python
def apply_tarpit(self):
    print(f"[*] Engaging Tarpit Defense...")
    time.sleep(5) # Wastes attacker resources
```
This simple blocking call prevents the Python thread from responding immediately, effectively paralyzing the attacker's automated scanning script.

### 5.3 Automated OSINT Profiling
The Bash script acts as a daemon, using `tail -F` to stream logs. It uses `awk` and `grep` to extract IP addresses. To prevent API rate-limiting, an IP cache (`profiled_ips.txt`) is maintained. 
The system uses `curl` to fetch JSON data from `ipinfo.io`, parsing out the `City`, `Country`, and `ISP/Org` of the attacker, enriching the raw IP address into actionable Threat Intelligence.

---

## 6. Testing and Results

### 6.1 Test Case 1: Credential Stuffing
- **Action:** Sent an HTTP POST request containing `username=admin&password=hacker123`.
- **System Response:** The DPI engine found no malicious code but recognized the brute-force attempt. It logged the exact credentials and tagged the attack as `[BRUTEFORCE]`.

### 6.2 Test Case 2: Cross-Site Scripting (XSS) Payload
- **Action:** Sent an HTTP GET request to `/?search=<script>alert(1)</script>`.
- **System Response:** The Regex engine immediately flagged the payload. The system tagged it as `[XSS_SCRIPTING]` and engaged the Tarpit defense, hanging the connection for 5 seconds.

### 6.3 Test Case 3: OSINT Resolution
- **Action:** A remote IP (e.g., `8.8.8.8`) triggered an alert.
- **System Response:** The Bash profiler instantly resolved the IP to its geographic location and ISP (e.g., Google LLC), successfully generating a new row in the live HTML dashboard.

---

## 7. Future Enhancements
While WebTrap is highly effective in its current state, future iterations could include:
1. **Automated Null-Routing:** Integrating the Bash script with Linux `iptables` or `ufw` to automatically drop all future packets from a profiled IP at the kernel level.
2. **Machine Learning DPI:** Replacing the static Regex signatures with an anomaly-detection machine learning model to catch zero-day payloads.
3. **Multi-Protocol Deception:** Expanding the Python server to host fake SSH (Port 22) and FTP (Port 21) services to trap a wider variety of botnets.

---

## 8. Conclusion
The WebTrap project successfully proves that advanced, enterprise-grade security concepts—such as Deception Technology, Deep Packet Inspection, and Automated Threat Profiling—can be engineered using lightweight scripting languages without heavy dependencies. By shifting the paradigm from passive blocking to active retaliation and intelligence gathering, WebTrap represents a highly effective framework for modern cybersecurity defense.
