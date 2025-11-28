#!/bin/bash

# HQMX Server Dependencies Setup Script
# Installs necessary system packages and tools on the EC2 instance.

set -e

# Configuration
EC2_HOST="23.21.183.81"
EC2_USER="ubuntu"
SSH_KEY="hqmx-ec2.pem"

echo "============================================"
echo "🛠️  HQMX Server Dependencies Setup"
echo "============================================"

# Check SSH Key
if [ ! -f "$SSH_KEY" ]; then
    if [ -f "../$SSH_KEY" ]; then
        SSH_KEY="../$SSH_KEY"
    else
        echo "❌ Error: SSH key '$SSH_KEY' not found!"
        exit 1
    fi
fi

echo "Connecting to $EC2_USER@$EC2_HOST..."

ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << 'EOF'
    set -e
    
    echo "🔄 Updating package lists..."
    sudo apt-get update
    
    echo "📦 Installing System Dependencies..."
    sudo apt-get install -y python3-pip python3-venv nginx ffmpeg unzip
    
    echo "📦 Installing Node.js (LTS)..."
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo "   Node.js is already installed: $(node -v)"
    fi
    
    echo "📦 Installing PM2 (Global)..."
    if ! command -v pm2 &> /dev/null; then
        sudo npm install -g pm2
    else
        echo "   PM2 is already installed: $(pm2 -v)"
    fi

    echo "📦 Installing yt-dlp..."
    if ! command -v yt-dlp &> /dev/null; then
        sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
        sudo chmod a+rx /usr/local/bin/yt-dlp
    else
        echo "   yt-dlp is already installed: $(yt-dlp --version)"
    fi

    echo "✅ Dependencies installation complete!"
EOF
