#!/bin/bash
# WiFi Configuration Portal - Installation Script for Raspberry Pi
# This script installs and configures the WiFi portal on your Raspberry Pi

set -e

echo "=========================================="
echo "WiFi Configuration Portal Installer"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
apt-get update

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    network-manager \
    wireless-tools \
    iw \
    hostapd \
    dnsmasq

# Enable NetworkManager if not already enabled
systemctl enable NetworkManager
systemctl start NetworkManager

# Create portal directory
PORTAL_DIR="/opt/wifi-portal"
echo -e "${YELLOW}Creating portal directory at $PORTAL_DIR...${NC}"
mkdir -p $PORTAL_DIR
mkdir -p $PORTAL_DIR/templates

# Note: The actual files will be copied by the user or via SCP
# This script creates the service file and configures the system

# Create systemd service file
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/wifi-portal.service << 'EOF'
[Unit]
Description=WiFi Configuration Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wifi-portal
Environment="PATH=/opt/wifi-portal/venv/bin"
ExecStart=/opt/wifi-portal/venv/bin/python /opt/wifi-portal/wifi_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create virtual environment and install dependencies
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
if [ -f "$PORTAL_DIR/requirements.txt" ]; then
    python3 -m venv $PORTAL_DIR/venv
    $PORTAL_DIR/venv/bin/pip install --upgrade pip
    $PORTAL_DIR/venv/bin/pip install -r $PORTAL_DIR/requirements.txt
fi

# Create a simple standalone server as fallback
cat > $PORTAL_DIR/start-portal.sh << 'EOF'
#!/bin/bash
# Start the WiFi portal manually
cd /opt/wifi-portal
source venv/bin/activate
sudo python3 wifi_server.py
EOF
chmod +x $PORTAL_DIR/start-portal.sh

# Configure network interfaces
echo -e "${YELLOW}Configuring network...${NC}"

# Backup original config
cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup 2>/dev/null || true

# Add static IP configuration for AP mode (optional - for standalone AP mode)
# Uncomment the following if you want the Pi to act as an AP
cat >> /etc/dhcpcd.conf << 'EOF'

# WiFi Portal Static IP (for AP mode)
# Uncomment these lines if you want the Pi to create its own WiFi network
# interface wlan0
# static ip_address=192.168.4.1/24
# nohook wpa_supplicant
EOF

# Configure dnsmasq for DHCP (optional - for AP mode)
cat > /etc/dnsmasq.conf.wifi-portal << 'EOF'
# WiFi Portal DHCP Configuration
# Uncomment to enable AP mode with DHCP
# interface=wlan0
# dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Create hostapd configuration template
cat > /etc/hostapd/hostapd.conf.wifi-portal << 'EOF'
# WiFi Portal Access Point Configuration
# Uncomment to enable AP mode
# interface=wlan0
# driver=nl80211
# ssid=PiWiFi-Setup
# hw_mode=g
# channel=7
# wmm_enabled=0
# macaddr_acl=0
# auth_algs=1
# ignore_broadcast_ssid=0
# wpa=2
# wpa_passphrase=raspberry
# wpa_key_mgmt=WPA-PSK
# wpa_pairwise=TKIP
# rsn_pairwise=CCMP
EOF

# Allow pi user to run nmcli without password
echo -e "${YELLOW}Configuring user permissions...${NC}"
cat > /etc/sudoers.d/wifi-portal << 'EOF'
# Allow pi user to manage WiFi without password
pi ALL=(ALL) NOPASSWD: /usr/bin/nmcli
pi ALL=(ALL) NOPASSWD: /sbin/iw
pi ALL=(ALL) NOPASSWD: /sbin/ifconfig
pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart wifi-portal
EOF
chmod 440 /etc/sudoers.d/wifi-portal

# Enable IP forwarding (for AP mode)
echo -e "${YELLOW}Configuring IP forwarding...${NC}"
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# Configure firewall rules
cat > /opt/wifi-portal/setup-firewall.sh << 'EOF'
#!/bin/bash
# Setup firewall rules for WiFi portal

# Allow traffic on portal port
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Allow DHCP
iptables -A INPUT -p udp --dport 67:68 -j ACCEPT

# Allow DNS
iptables -A INPUT -p udp --dport 53 -j ACCEPT

# Save rules
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
EOF
chmod +x /opt/wifi-portal/setup-firewall.sh

# Reload systemd
echo -e "${YELLOW}Reloading systemd...${NC}"
systemctl daemon-reload

# Enable service
systemctl enable wifi-portal

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Portal files location: $PORTAL_DIR"
echo ""
echo "To complete setup:"
echo "1. Copy wifi_server.py to $PORTAL_DIR/"
echo "2. Copy templates/wifi_portal.html to $PORTAL_DIR/templates/"
echo "3. Copy requirements.txt to $PORTAL_DIR/"
echo "4. Run: cd $PORTAL_DIR && sudo ./install.sh"
echo "5. Start the portal: sudo systemctl start wifi-portal"
echo ""
echo "Access the portal at:"
echo "  - http://192.168.29.115 (if connected to network)"
echo "  - http://raspberrypi.local (if mDNS is available)"
echo ""
echo "Service commands:"
echo "  sudo systemctl start wifi-portal   # Start"
echo "  sudo systemctl stop wifi-portal    # Stop"
echo "  sudo systemctl status wifi-portal  # Check status"
echo ""
