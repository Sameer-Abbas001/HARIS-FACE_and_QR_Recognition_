#!/usr/bin/env bash
# Quick local / server setup script
set -e
echo "Installing HARIS dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed successfully!"
echo "To run the Web App: python3 web_app.py"
