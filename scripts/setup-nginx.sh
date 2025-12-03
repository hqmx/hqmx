#!/bin/bash

# HQMX Nginx Setup Script
# Uploads and configures Nginx for API routing.

set -e

# Configuration
EC2_HOST="23.21.183.81"
EC2_USER="ubuntu"
SSH_KEY="/Users/wonjunjang/hqmx/converter/hqmx-ec2.pem"
LOCAL_CONF="hqmx_nginx_config.conf"

echo "============================================"
echo "🌐 HQMX Nginx Configuration Setup"
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

# Check Config File
if [ ! -f "$LOCAL_CONF" ]; then
    echo "❌ Error: Nginx config file '$LOCAL_CONF' not found!"
    exit 1
fi

echo "Connecting to $EC2_USER@$EC2_HOST..."

# 1. Upload Config
echo "📤 Uploading Nginx configuration..."
scp -i "$SSH_KEY" "$LOCAL_CONF" "$EC2_USER@$EC2_HOST:/home/$EC2_USER/hqmx.net.conf"

# 2. Apply Config
echo "⚙️  Applying Nginx configuration..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << 'EOF'
    set -e
    
    echo "   Moving config to /etc/nginx/sites-available/..."
    sudo mv ~/hqmx.net.conf /etc/nginx/sites-available/hqmx.net
    
    echo "   Enabling site..."
    sudo ln -sf /etc/nginx/sites-available/hqmx.net /etc/nginx/sites-enabled/
    
    # Remove default if it exists (optional, but recommended to avoid conflicts)
    if [ -f /etc/nginx/sites-enabled/default ]; then
        echo "   Removing default site..."
        sudo rm /etc/nginx/sites-enabled/default
    fi
    
    echo "   Testing Nginx configuration..."
    sudo nginx -t
    
    echo "   Reloading Nginx..."
    sudo systemctl reload nginx
    
    echo "✅ Nginx configured successfully!"
EOF
