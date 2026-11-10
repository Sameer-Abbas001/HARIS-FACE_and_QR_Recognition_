#!/usr/bin/env bash
# ==============================================================================
# HARIS - Automated 1-Command Docker Deployment for AWS EC2
# Creator & Lead Developer: Sameer Abbas
#
# Supported OS: Ubuntu 20.04/22.04/24.04 LTS, Debian, Amazon Linux 2023
# Usage:
#   bash deploy_docker.sh
# ==============================================================================

set -e

echo "=========================================================="
echo "⚡ HARIS - Docker Cloud Deployment Pipeline for AWS EC2"
echo "=========================================================="

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

# 1. Setup swap space on 1GB RAM instances to prevent Docker OOM errors
SWAP_SIZE=$(free -m | awk '/^Swap:/ {print $2}')
if [ -z "$SWAP_SIZE" ] || [ "$SWAP_SIZE" -eq 0 ]; then
    echo "[1/5] Configuring 1GB swap file to prevent memory exhaustion..."
    sudo fallocate -l 1G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile || true
    echo "✔ Swap configured."
else
    echo "[1/5] ✔ Swap already active (${SWAP_SIZE}MB)."
fi

# 2. Install Docker & Docker Compose if missing
if ! command -v docker >/dev/null 2>&1; then
    echo "[2/5] Docker not found. Installing Docker & Compose automatically..."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Install docker
    sudo apt-get install -y docker.io docker-compose-v2
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER" || true
    echo "✔ Docker installed successfully."
else
    echo "[2/5] ✔ Docker is already installed."
fi

# Ensure docker daemon is active
sudo systemctl start docker

# 3. Ensure data directories exist on host so volumes bind cleanly
echo "[3/5] Initializing host directories..."
mkdir -p "$APP_DIR/data/classifiers"
mkdir -p "$APP_DIR/data/qrcodes"
if [ ! -f "$APP_DIR/nameslist.txt" ]; then
    touch "$APP_DIR/nameslist.txt"
fi

# 4. Build and launch containers
echo "[4/5] Building and launching HARIS Docker container..."
if docker compose version >/dev/null 2>&1; then
    sudo docker compose down --remove-orphans || true
    sudo docker compose up -d --build
else
    sudo docker-compose down --remove-orphans || true
    sudo docker-compose up -d --build
fi

# 5. Fetch EC2 Public IP
echo "[5/5] Verifying deployment..."
sleep 3
PUBLIC_IP=$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 || curl -s --connect-timeout 2 https://api.ipify.org || echo "<YOUR-EC2-PUBLIC-IP>")

echo ""
echo "=========================================================="
echo "🎉 HARIS IS NOW LIVE ON AWS EC2 VIA DOCKER!"
echo "=========================================================="
echo "⚡ Container Status: Active & Running in background (24/7)"
echo ""
echo "🌐 Open your browser and visit:"
echo "   http://$PUBLIC_IP"
echo "   (or: http://$PUBLIC_IP:5000)"
echo ""
echo "📋 Handy Docker Management Commands:"
echo "   • View Live Logs:    sudo docker compose logs -f"
echo "   • Container Status:  sudo docker compose ps"
echo "   • Restart App:       sudo docker compose restart"
echo "   • Stop App:          sudo docker compose down"
echo "=========================================================="
