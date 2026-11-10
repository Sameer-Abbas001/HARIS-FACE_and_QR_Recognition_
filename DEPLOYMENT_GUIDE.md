# 🚀 HARIS - AWS EC2 Deployment Guide

> **High-Accuracy Recognition & Identity System**  
> Complete, production-ready guide for deploying HARIS on an AWS EC2 instance.

---

## 📋 Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Step 1: Launch an AWS EC2 Instance](#step-1-launch-an-aws-ec2-instance)
4. [Step 2: Configure AWS Security Group (Firewall)](#step-2-configure-aws-security-group-firewall)
5. [Step 3: Connect to EC2 & Upload Code](#step-3-connect-to-ec2--upload-code)
6. [Step 4: Deploy using Automated Script (Recommended)](#step-4-deploy-using-automated-script-recommended)
7. [Alternative: Deploy with Docker & Docker Compose](#alternative-deploy-with-docker--docker-compose)
8. [Managing the HARIS Systemd Service](#managing-the-haris-systemd-service)
9. [Optional: Production Domain & Free SSL (Nginx + Let's Encrypt)](#optional-production-domain--free-ssl-nginx--lets-encrypt)
10. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## 1. Architecture Overview

When deployed on AWS EC2, HARIS operates headlessly in the cloud:
- **Web Interface**: Powered by **Flask + React** on port `5000`. Accessible from any browser (desktop, smartphone, tablet).
- **Camera & Biometrics**: Browser webcam capture (`st.camera_input`) or snapshot uploads are streamed securely to the server.
- **Biometric Engine**: OpenCV LBPH (Local Binary Pattern Histograms) + Haar Cascade classifiers.
- **Access Passes**: Photo-embedded high-ECC QR codes + cybernetic holographic badges generated and downloadable directly from the dashboard.
- **Auto-Recovery**: Managed via Linux `systemd` service for 24/7 uptime and automatic restart upon crash or reboot.

---

## 2. Prerequisites
- An active AWS Account.
- Key Pair (`.pem` file) for SSH authentication.
- Git or SCP/FileZilla to transfer project files.

---

## Step 1: Launch an AWS EC2 Instance

1. Open the [AWS Management Console](https://console.aws.amazon.com/ec2).
2. Click **Launch Instance**.
3. **Name**: `HARIS-Biometric-Server`
4. **Application and OS Images (AMI)**: Select **Ubuntu Server 24.04 LTS** or **Ubuntu 22.04 LTS** (64-bit x86).
5. **Instance Type**:
   - `t2.micro` (AWS Free Tier eligible - suitable for testing).
   - `t3.small` or `t3.medium` (Recommended for production multi-user inference).
6. **Key Pair**: Select your existing key pair or create a new one (e.g., `haris-key.pem`).
7. **Storage**: 15 GB – 20 GB gp3 SSD.

---

## Step 2: Configure AWS Security Group (Firewall)

Under **Network Settings** -> **Security Group Rules**, ensure the following inbound ports are open:

| Type | Port Range | Protocol | Source | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **SSH** | `22` | TCP | `My IP` or `0.0.0.0/0` | Terminal remote access |
| **Custom TCP** | `5000` | TCP | `0.0.0.0/0` (Anywhere) | **HARIS Web Dashboard** |
| **HTTP** | `80` | TCP | `0.0.0.0/0` (Anywhere) | Optional Nginx reverse proxy |
| **HTTPS** | `443` | TCP | `0.0.0.0/0` (Anywhere) | Optional SSL certificate |

> [!IMPORTANT]
> Port **5000** must be open in your Security Group to access the web application directly in your browser.

---

## Step 3: Connect to EC2 & Upload Code

### Option A: Via SSH & Git (Fastest)
1. Connect to your instance via terminal:
   ```bash
   chmod 400 haris-key.pem
   ssh -i "haris-key.pem" ubuntu@<YOUR-EC2-PUBLIC-IP>
   ```
2. Clone your repository:
   ```bash
   git clone <YOUR-GITHUB-REPO-URL> HARIS
   cd HARIS
   ```

### Option B: Via SCP / File Transfer
From your local computer:
```bash
scp -i "haris-key.pem" -r HARIS ubuntu@<YOUR-EC2-PUBLIC-IP>:~/
```
Then SSH in:
```bash
ssh -i "haris-key.pem" ubuntu@<YOUR-EC2-PUBLIC-IP>
cd HARIS
```

---

## Step 4: Deploy using Automated Script (Recommended)

Run the automated direct deployment script:

```bash
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

### What `deploy_ec2.sh` does automatically:
1. Updates package repositories (`apt-get update`).
2. Installs Python 3, `pip`, `venv`, compiler tools, and OpenCV headless system libraries (`libgl1`, `libglib2.0-0`, `fonts-dejavu-core`).
3. Creates a Python virtual environment (`venv/`).
4. Installs all updated, modern dependencies from `requirements.txt`.
5. Configures and registers a `systemd` background service (`haris.service`).
6. Starts HARIS immediately and sets it to auto-restart on system reboot.

### Accessing the Web Application:
Open your browser and navigate to:
```
http://<YOUR-EC2-PUBLIC-IP>:5000
```

---

## Alternative: Deploy with Docker & Docker Compose

If you prefer containerized deployment:

1. Install Docker & Docker Compose on your EC2:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose-v2
   sudo usermod -aG docker ubuntu
   newgrp docker
   ```
2. Launch the container:
   ```bash
   docker compose up -d --build
   ```
3. Check container status:
   ```bash
   docker compose ps
   docker compose logs -f
   ```

---

## Managing the HARIS Systemd Service

When deployed with `deploy_ec2.sh`, HARIS runs continuously in the background via systemd:

```bash
# Check service status
sudo systemctl status haris

# View real-time application logs
sudo journalctl -u haris -f

# Restart the application
sudo systemctl restart haris

# Stop the application
sudo systemctl stop haris

# Start the application
sudo systemctl start haris
```

---

## Optional: Production Domain & Free SSL (Nginx + Let's Encrypt)

To serve HARIS on standard port 80/443 with HTTPS and your custom domain name:

1. Install Nginx and Certbot:
   ```bash
   sudo apt-get install -y nginx certbot python3-certbot-nginx
   ```
2. Copy the included Nginx config:
   ```bash
   sudo cp nginx_haris.conf /etc/nginx/sites-available/haris
   sudo ln -s /etc/nginx/sites-available/haris /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t
   sudo systemctl restart nginx
   ```
3. Install free SSL certificate (requires your domain to point to your EC2 Public IP):
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

Your app is now securely live at `https://yourdomain.com`!

---

## Troubleshooting & FAQ

### Q: The browser shows "This site can't be reached" when visiting `http://<EC2-IP>:5000`.
- **Cause**: Port 5000 is blocked in your AWS EC2 Security Group.
- **Fix**: Go to AWS EC2 Console -> Instances -> Click your instance -> Security tab -> Click Security Group -> **Edit Inbound Rules** -> Add Rule: Custom TCP, Port 5000, Source `0.0.0.0/0`.

### Q: How does camera capture work without a webcam physically plugged into the EC2 server?
- **Answer**: `web_app.py` runs in your web browser. When you click **Capture Photo**, your browser securely streams video from your local device camera (laptop/smartphone) to the HARIS cloud endpoint for instant biometric matching.

### Q: Where are newly registered users and models stored?
- All data persists in `./data/`:
  - `data/<username>/`: 50 biometric face training frames.
  - `data/classifiers/<username>_classifier.xml`: Compiled LBPH model.
  - `data/qrcodes/`: Photo-embedded QR passes and cybernetic ID badges.
  - `nameslist.txt`: Master user registry index.

