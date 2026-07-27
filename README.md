# WebTrap: Active Web-Based Honeypot & Threat Profiler

WebTrap is a final year cybersecurity project designed to act as an active defense mechanism. It combines a Python-based web honeypot to lure attackers and a Bash-based threat profiler to analyze and automatically block malicious traffic.

## Features
- **Fake Web Server (Python):** Simulates a vulnerable administrator login panel to attract automated scanners and malicious actors.
- **Silent Logging:** Captures attacker IP addresses, requested paths, HTTP headers, and submitted credentials without tipping off the attacker.
- **Threat Profiling (Bash):** Continuously monitors honeypot logs, extracts attacker IPs, performs OSINT lookups (geolocation, ASN mapping), and logs their profile.
- **Active Defense:** Can be configured to automatically block malicious IPs using OS-level firewalls (`iptables`).

## Project Structure
```
WebTrap/
│
├── webtrap.py          # The core Python honeypot server
├── profiler.sh         # The Bash threat profiling & defense script
├── html/               # Directory containing the fake web pages
│   └── index.html      # Fake Admin Login Page
├── logs/               # Directory where attacker activity is recorded
│   └── honeypot.log    # Main log file
└── README.md           # Project documentation
```

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/WebTrap.git
   cd WebTrap
   ```

2. **Make the Bash script executable:**
   ```bash
   chmod +x profiler.sh
   ```

3. **Run the Honeypot (Terminal 1):**
   ```bash
   python3 webtrap.py
   ```
   *The fake server will start on port 8080 by default.*

4. **Run the Threat Profiler (Terminal 2):**
   ```bash
   ./profiler.sh
   ```
   *The script will now monitor the honeypot.log in real-time.*

## How to Test It Locally
1. Start both the Python server and the Bash script as shown above.
2. Open your web browser and go to `http://localhost:8080`.
3. Try to log in with a fake username (e.g., `admin`) and password (e.g., `password123`).
4. Look at your terminal! You will see the Python script catch the credentials, and the Bash script immediately profile your local IP address.

## Technologies Used
- **Python 3:** `http.server`, `socket`, `logging` (No external libraries required!)
- **Bash:** `awk`, `grep`, `curl`, `jq` (for interacting with OSINT APIs)

## Disclaimer
This project is intended for educational purposes and academic research only. Do not deploy the automated blocking features (`iptables`) on production networks without proper authorization and fail-safes.
