#!/usr/bin/env bash
# ==============================================================================
# HARIS - Automated AWS EC2 Direct Deployment Script
# Creator & Lead Developer: Sameer Abbas
#
# Supported OS: Ubuntu 20.04 / 22.04 / 24.04 LTS, Debian 11/12
# Usage:
#   1. As EC2 User Data script upon instance launch, OR
#   2. Run via SSH: bash deploy_ec2.sh
# ==============================================================================

set -e

echo "=========================================================="
echo "⚡ HARIS - High-Accuracy Recognition & Identity System"
echo "🚀 Initiating AWS EC2 Deployment Pipeline..."
echo "=========================================================="

# 1. Determine installation directory and user
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="$(whoami)"

echo "[1/6] Target Application Directory: $APP_DIR"
echo "[1/6] Running as user: $CURRENT_USER"

# 2. Update system packages and install required dependencies
echo "[2/6] Updating APT repositories and installing prerequisites..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu-core

# 3. Create and activate Python virtual environment
echo "[3/6] Configuring Python virtual environment..."
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv
source "$APP_DIR/venv/bin/activate"

# 4. Install Python dependencies
echo "[4/6] Installing dependencies from requirements.txt..."
pip install --upgrade pip setuptools wheel
pip install -r "$APP_DIR/requirements.txt"

# Ensure data directories exist
mkdir -p "$APP_DIR/data/classifiers"
mkdir -p "$APP_DIR/data/qrcodes"

# 5. Create Systemd Service for 24/7 background operation & auto-restart
echo "[5/6] Creating Systemd Service 'haris.service'..."
SERVICE_FILE="/etc/systemd/system/haris.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=HARIS Biometric & QR Access Intelligence Web Core
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python3 web_app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable haris.service
sudo systemctl restart haris.service

# 6. Configure Firewall if UFW is active
if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 5000/tcp comment 'HARIS Web App' || true
fi

# Retrieve Public IP for easy user access
PUBLIC_IP=$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 || curl -s --connect-timeout 2 https://api.ipify.org || echo "<YOUR-EC2-PUBLIC-IP>")

echo ""
echo "=========================================================="
echo "🎉 DEPLOYMENT COMPLETE & SERVICE ACTIVE!"
echo "=========================================================="
echo "⚡ HARIS is running in the background via Systemd."
echo ""
echo "🌐 Access your live web application at:"
echo "   http://$PUBLIC_IP:5000"
echo ""
echo "📋 System Management Commands:"
echo "   • Check Status:   sudo systemctl status haris"
echo "   • View Live Logs: sudo journalctl -u haris -f"
echo "   • Restart App:    sudo systemctl restart haris"
echo "   • Stop App:       sudo systemctl stop haris"
echo "=========================================================="

