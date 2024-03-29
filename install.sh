#!/usr/bin/env bash

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 
    exit 1
fi

# When a command fails, bash exits instead of continuing with the rest of the script
set -o errexit

# Script fails, when accessing an unset variable
set -o nounset

# Pipeline command is treated as failed, even if one command in the pipeline fails
set -o pipefail

# Enable debug mode with TRACE=1
if [[ "${TRACE-0}" == "1" ]]; then
    set -o xtrace
fi

# Postion yourself in script directory
cd "$(dirname "$0")"

# Setup nftables

# Flush existing rules
nft flush ruleset

# Create table 
nft add table inet filter

# Create chain consul which will be dynamically populated
nft add chain inet filter consul { type filter hook input priority 0\; policy accept\; }

# Define the second chain for security
nft add chain inet filter security { type filter hook input priority 50\; policy accept\; }

# Add rules to the security chain
nft add rule inet filter security ct state established,related counter accept
nft add rule inet filter security iif lo accept
nft add rule inet filter security meta mark 0x1 accept
nft add rule inet filter security meta nfproto ipv4 icmp type { echo-request } counter accept
nft add rule inet filter security meta nfproto ipv6 icmpv6 type echo-request counter accept
nft add rule inet filter security meta nfproto ipv6 icmpv6 type { nd-neighbor-advert, nd-neighbor-solicit, nd-router-advert} ip6 hoplimit 1 accept
nft add rule inet filter security meta nfproto ipv6 icmpv6 type { nd-neighbor-advert, nd-neighbor-solicit, nd-router-advert} ip6 hoplimit 255 counter accept
nft add rule inet filter security tcp dport 22 ct state new tcp flags \& \(syn \| ack\) == syn counter accept
nft add rule inet filter security ip saddr 10.10.0.0/16 tcp dport { 8300, 8301, 8302, 8600 } accept
nft add rule inet filter security tcp dport 0-65535 reject
nft add rule inet filter security udp dport 0-65535 counter drop
nft add rule inet filter security counter drop

# Save the initial set of rules in the case of restart
nft list ruleset > /etc/nftables.conf

echo "Rules applied successfully."

# Install python packages required by the script
pip install -r requirements.txt

# Create a folder if it is not already present for our script
mkdir -p /opt/scripts/
cp firewall_updater.py /opt/scripts/

LOG_FILE="/var/log/firewall_updater.log"
COMMAND="python3 /opt/scripts/firewall_updater.py"

touch $LOG_FILE

# Add the cron job
(crontab -l ; echo "0 * * * * $COMMAND >> $LOG_FILE 2>&1") | crontab -
