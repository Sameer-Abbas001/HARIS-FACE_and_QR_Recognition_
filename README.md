# ⚡ HARIS - High-Accuracy Recognition & Identity System

> **AI-Powered Dual Biometric Face Recognition & Photo-Embedded QR Access Control**  
> **Developed & Built by Sameer Abbas**

---

## 🌟 Overview

**HARIS** is an intelligent access control and identity verification suite built in Python. It provides high-speed, dual-mode security combining real-time **Local Binary Pattern Histograms (LBPH)** facial recognition with **high-error-correction QR codes** embedded with registered user portrait photos.

Developed and engineered by **Sameer Abbas**.

---

## 🚀 Key Features

- **⚡ High-Speed Dataset Enrollment (4 Frames)**: Rapid face capture with real-time OpenCV HUD bounding indicators.
- **🧠 Custom Neural Classifier Training**: One-click local training with immediate LBPH face model generation.
- **🪪 Photo-Embedded QR Badge Generation**: Generates high-error-correction QR codes with integrated user portrait photos and cybernetic ID badges.
- **🎯 Dual-Mode Biometric & QR Verification**: Simultaneous face recognition and QR scanning with a futuristic cyberpunk HUD overlay.
- **🎨 Glassmorphic Cyberpunk GUI**: Modern animated particle canvas background, smooth color fading, glowing neon indicators, and live system telemetry.

---

## 📦 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Web Application (Recommended for Cloud / AWS EC2 / Local)
```bash
python web_app.py
```
> Access at: `http://localhost:5000` or `http://<EC2-PUBLIC-IP>:5000`

### 3. Launch Desktop GUI (For Local Desktop with Display)
```bash
python app-gui.py
```

---

## ☁️ AWS EC2 Direct Cloud Deployment

HARIS is fully optimized for **direct 1-command deployment on AWS EC2**:

```bash
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

- Installs all dependencies and system libraries automatically.
- Registers a `systemd` service (`haris.service`) for 24/7 background operation and auto-restart.
- Or deploy using Docker Compose:
  ```bash
  docker compose up -d --build
  ```
- See the full [AWS EC2 Deployment Guide](file:///c:/Users/sameer/Downloads/HARIS/DEPLOYMENT_GUIDE.md) for step-by-step instructions.

---

## 🛠️ System Architecture & Workflow

1. **User Registration**: Add user profile and capture 50 face frames.
2. **Model Training**: Train and compile local LBPH facial biometric classifier models.
3. **QR Badge Generation**: Automatically generates photo-embedded QR codes and full cybernetic ID badges.
4. **Access Core**: Launch live dual-recognition HUD to verify identity and grant access.

---

## 👤 Author & Builder

- **Developer**: **Sameer Abbas**
- **Project**: HARIS Biometric Access Intelligence Core

Made with ❤ by **Sameer Abbas**
