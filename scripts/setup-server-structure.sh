#!/bin/bash

# HQMX Server Structure Setup Script
# 이 스크립트는 EC2 서버에 표준 디렉토리 구조를 생성합니다.

set -e

# Configuration
EC2_HOST="23.21.183.81"
EC2_USER="ubuntu"
SSH_KEY="hqmx-ec2.pem"
BASE_DIR="/home/ubuntu/hqmx"

echo "============================================"
echo "🏗️  HQMX Server Structure Setup"
echo "============================================"
echo "Target: $EC2_USER@$EC2_HOST"
echo "Base Dir: $BASE_DIR"
echo "--------------------------------------------"

# 1. Check SSH Key
if [ ! -f "$SSH_KEY" ]; then
    if [ -f "../$SSH_KEY" ]; then
        SSH_KEY="../$SSH_KEY"
    else
        echo "❌ Error: SSH key '$SSH_KEY' not found!"
        exit 1
    fi
fi

# 2. Define Services
SERVICES=("downloader" "converter" "calculator" "generator")

# 3. Create Directory Structure
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
    set -e
    
    echo "📂 Creating base directories..."
    mkdir -p $BASE_DIR/services
    mkdir -p $BASE_DIR/shared

    for SERVICE in ${SERVICES[@]}; do
        echo "   - Setting up \$SERVICE..."
        
        # Create Service Directories
        mkdir -p $BASE_DIR/services/\$SERVICE/releases
        mkdir -p $BASE_DIR/shared/\$SERVICE/logs
        
        # Create dummy .env if not exists (for backend services)
        if [ ! -f "$BASE_DIR/shared/\$SERVICE/.env" ]; then
            touch "$BASE_DIR/shared/\$SERVICE/.env"
        fi
    done

    echo "✅ Directory structure created successfully!"
    
    echo "🔍 Current Structure:"
    tree -L 3 $BASE_DIR || ls -R $BASE_DIR
EOF

echo ""
echo "🎉 Setup Complete! You can now use ./scripts/deploy-modular.sh"
