#!/use/bin/env bash

# WebTrap Threat Profiler
# Continuous monitoring and OSINT gathering

LOG_FILE="logs/honeypot.log"
PROFILED_IPS="logs/profiled_ips.txt"
REPORT_FILE="logs/threat_report.html"

# Email Alert Configuration (reuses same env vars as webtrap.py)
SENDER_EMAIL="${WEBTRAP_SENDER_EMAIL:-}"
SENDER_PASSWORD="${WEBTRAP_SENDER_PASSWORD:-}"
RECEIVER_EMAIL="${WEBTRAP_RECEIVER_EMAIL:-}"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="465"

mkdir -p logs
touch "$LOG_FILE" "$PROFILED_IPS"

send_email_alert() {
    local ip="$1"
    local location="$2"
    local tags="$3"

    # Skip silently if not configured
    if [ -z "$SENDER_EMAIL" ] || [ -z "$SENDER_PASSWORD" ] || [ -z "$RECEIVER_EMAIL" ]; then
        return
    fi

    local tmp_mail
    tmp_mail=$(mktemp)

    cat <<MAILEOF > "$tmp_mail"
From: WebTrap Honeypot <$SENDER_EMAIL>
To: $RECEIVER_EMAIL
Subject: [WebTrap ALERT] Threat Profiled - $ip

WebTrap has profiled a new attacker.

Attacker IP: $ip
Location/ISP: $location
Threat Signatures: $tags
Time: $(date '+%Y-%m-%d %H:%M:%S')

Full report: logs/threat_report.html
MAILEOF

    # Send via curl SMTP, in the background so it never blocks monitoring
    (
        curl -s --url "smtps://${SMTP_HOST}:${SMTP_PORT}" --ssl-reqd \
            --mail-from "$SENDER_EMAIL" \
            --mail-rcpt "$RECEIVER_EMAIL" \
            --upload-file "$tmp_mail" \
            --user "${SENDER_EMAIL}:${SENDER_PASSWORD}" \
            > /dev/null 2>&1
        rm -f "$tmp_mail"
    ) &
}

clear
echo "==================================================="
echo "    ADVANCED THREAT PROFILER INITIALIZED           "
echo "    Monitoring network traffic in real-time        "
echo "==================================================="

# Initialize Dynamic HTML Report
cat <<EOF > "$REPORT_FILE"
<!DOCTYPE html>
<html>
<head>
    <title>WebTrap Live Threat Report</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: 'Courier New', Courier, monospace; background: #0d1117; color: #c9d1d9; margin: 2rem; }
        h1 { color: #ff7b72; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #30363d; }
        th { background: #161b22; color: #58a6ff; }
        .tag { background: #ff7b72; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    </style>
</head>
<body>
    <h1>WebTrap Live Threat Report</h1>
    <p>Auto-generated intelligence report. Refreshes every 5 seconds.</p>
    <table>
        <tr><th>Timestamp</th><th>Attacker IP</th><th>Location / ISP</th><th>Threat Signatures</th></tr>
EOF

# Process log file stream
tail -Fn0 "$LOG_FILE" | while read -r line; do
    
    if echo "$line" | grep -q "IP:"; then
        
        TIMESTAMP=$(echo "$line" | awk -F'|' '{print $1}')
        IP=$(echo "$line" | grep -o 'IP:[^ ]*' | cut -d':' -f2)
        TAGS=$(echo "$line" | grep -o 'TAGS:\[[^]]*\]' | cut -d'[' -f2 | cut -d']' -f1)
        
        if [ -z "$IP" ]; then
            continue
        fi

        if grep -q "^$IP$" "$PROFILED_IPS"; then
            continue
        fi
        
        echo "[!] CRITICAL ALERT: Malicious activity detected from $IP"
        echo "    -> Signatures Matched: [ $TAGS ]"
        
        if [ "$IP" = "127.0.0.1" ] || [ "$IP" = "::1" ]; then
            echo "    -> Origin: Localhost (Skipping OSINT resolution)"
            LOCATION="Local Network"
        else
            echo "    -> Executing OSINT Profiling..."
            OSINT_DATA=$(curl -s "http://ipinfo.io/$IP/json" || echo "{}")
            COUNTRY=$(echo "$OSINT_DATA" | grep -i '"country"' | cut -d '"' -f 4)
            CITY=$(echo "$OSINT_DATA" | grep -i '"city"' | cut -d '"' -f 4)
            ORG=$(echo "$OSINT_DATA" | grep -i '"org"' | cut -d '"' -f 4)
            
            if [ -z "$COUNTRY" ]; then
                LOCATION="Unknown Location"
            else
                LOCATION="$CITY, $COUNTRY ($ORG)"
            fi
            
            echo "    -> Target Identified: $LOCATION"

            send_email_alert "$IP" "$LOCATION" "$TAGS"

            # Active defense logic (disabled by default for safety)
            # echo "    -> Null-routing IP via iptables..."
            # sudo iptables -A INPUT -s $IP -j DROP
        fi
        
        echo "$IP" >> "$PROFILED_IPS"
        
        FORMATTED_TAGS=$(echo "$TAGS" | sed 's/,/<\/span> <span class="tag">/g')
        echo "<tr><td>$TIMESTAMP</td><td>$IP</td><td>$LOCATION</td><td><span class='tag'>$FORMATTED_TAGS</span></td></tr>" >> "$REPORT_FILE"
        
        echo "==================================================="
    fi
done