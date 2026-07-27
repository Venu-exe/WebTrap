# Final Year Project Report: WebTrap (Active Web-Based Honeypot & Threat Profiler)

## 1. Abstract
As cyber threats become increasingly automated, traditional passive defense mechanisms like static firewalls are often insufficient. This project proposes **WebTrap**, an active defense honeypot and threat intelligence profiler. Built using Python and Bash, WebTrap simulates a vulnerable enterprise gateway to lure automated scanners and malicious actors. Upon interaction, it utilizes Deep Packet Inspection (DPI) to categorize the attack (e.g., SQL Injection, XSS) and employs "Tarpitting" to degrade the attacker's resources. Concurrently, a Bash-based profiler extracts the attacker's IP, conducts OSINT gathering for geolocation and ISP tracing, and generates a dynamic HTML threat report.

## 2. Introduction
Web applications remain the primary vector for data breaches. Security Operations Centers (SOCs) are often overwhelmed by alert fatigue from traditional Intrusion Detection Systems (IDS). This project aims to demonstrate the efficacy of Deception Technology by deploying a lightweight, high-fidelity honeypot. By trapping attackers rather than just blocking them, organizations can gather actionable threat intelligence.

## 3. System Architecture & Methodology
The system is divided into two distinct components operating in tandem:
1. **The Lure & Trap Engine (Python):** 
   - A custom HTTP server that mimics an enterprise login portal. 
   - Implements Regex-based signature matching to identify malicious payloads.
   - Deploys Active Defense via connection hanging (Tarpitting) to waste attacker resources.
2. **The Intelligence Profiler (Bash):**
   - Monitors server logs asynchronously.
   - Extracts IP addresses and queries the `ipinfo.io` API.
   - Formats the intelligence into a dynamically refreshing HTML dashboard.

## 4. Implementation Highlights
- **Zero-Dependency Architecture:** The Python server relies entirely on standard libraries (`http.server`, `socketserver`, `re`), ensuring extreme portability and a minimal attack surface.
- **Robust Log Parsing:** The Bash profiler uses strict `awk` and `grep` pipelines to ensure resilience against malformed log entries injected by attackers.

## 5. Results & Evaluation
During localized testing, the honeypot successfully identified and categorized simulated attacks (Credential Stuffing and Cross-Site Scripting). The Tarpit engine effectively delayed HTTP responses by 5 seconds per malicious request, proving its ability to severely degrade automated scanning tools like DirBuster or Nmap. The dynamic HTML report generated successfully in real-time, providing immediate visibility into the attack source.

## 6. Conclusion
The WebTrap project successfully demonstrates that advanced enterprise security concepts—such as Deception Technology, Deep Packet Inspection, and Automated Threat Intelligence—can be implemented using fundamental scripting languages (Python and Bash). Future enhancements could include automated null-routing via `iptables` and integration with decentralized threat intelligence sharing platforms.
