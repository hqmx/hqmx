#!/bin/bash

# HQMX Modular Deployment Script
# Usage: ./deploy-modular.sh --service=<service_name> [--env=<prod|dev>]

set -e

# Configuration
EC2_HOST="23.21.183.81"
EC2_USER="ubuntu"
BASE_REMOTE_DIR="/home/ubuntu/hqmx/services"

# Resolve Script Directory and Root Directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSH_KEY="$PROJECT_ROOT/hqmx-ec2.pem"

# Parse Arguments
SERVICE=""
ENV="dev" # Default to dev for safety

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --service=*) SERVICE="${1#*=}"; shift ;;
        --env=*) ENV="${1#*=}"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
done

if [ -z "$SERVICE" ]; then
    echo "❌ Error: Service name is required. Use --service=<name>"
    echo "Available services: downloader-frontend, downloader-backend, converter, calculator, generator"
    exit 1
fi

# Define Local and Remote Paths based on Service
# ... (Previous code remains the same up to case statement)

# Define Local and Remote Paths based on Service
case $SERVICE in
    "main")
        LOCAL_DIR="main/frontend"
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/main"
        ;;
    "downloader")
        LOCAL_DIR="downloader/frontend"
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/downloader"
        ;;
    "downloader-frontend")
        LOCAL_DIR="downloader/frontend"
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/downloader"
        ;;
    "downloader-backend")
        LOCAL_DIR="downloader/backend"
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/downloader-backend"
        ;;
    "converter")
        LOCAL_DIR="converter/frontend" 
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/converter"
        ;;
    "converter-backend")
        LOCAL_DIR="converter/backend"
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/converter-backend"
        ;;
    "calculator")
        LOCAL_DIR="calculator/frontend"
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/calculator"
        ;;
    "generator")
        LOCAL_DIR="generator/frontend"
        REMOTE_SERVICE_DIR="$BASE_REMOTE_DIR/generator"
        ;;
    *)
        echo "❌ Error: Unknown service '$SERVICE'"
        exit 1
        ;;
esac

# Generate timestamp on SERVER to avoid timezone issues
TIMESTAMP=$(ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "date +%Y%m%d_%H%M%S")
RELEASE_DIR="$REMOTE_SERVICE_DIR/releases/$TIMESTAMP"

# Determine Symlink Target based on Env
if [[ "$ENV" == "prod" ]]; then
    LINK_NAME="current"
    echo "⚠️  DEPLOYING TO PRODUCTION (current) ⚠️"
else
    LINK_NAME="dev"
    echo "🧪 DEPLOYING TO DEVELOPMENT (dev) 🧪"
fi

TARGET_LINK="$REMOTE_SERVICE_DIR/$LINK_NAME"

echo "============================================"
echo "🚀 Deploying $SERVICE to $ENV environment"
echo "============================================"
echo "Local Dir: $LOCAL_DIR"
echo "Remote Dir: $RELEASE_DIR"
echo "Target Link: $TARGET_LINK"
echo "--------------------------------------------"

# 1. Check SSH Key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found at: $SSH_KEY"
    echo "Please ensure 'hqmx-ec2.pem' exists in the project root."
    exit 1
fi

# 2. Create Remote Directories
echo "📂 Creating remote directories..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "mkdir -p $REMOTE_SERVICE_DIR/releases $REMOTE_SERVICE_DIR/shared"

# 3. Upload Files
echo "📦 Uploading files to new release folder..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "mkdir -p $RELEASE_DIR"

EXCLUDE_FLAGS="--exclude node_modules --exclude venv --exclude .git --exclude .DS_Store --exclude .next --exclude .cache --exclude __pycache__"

if command -v rsync &> /dev/null; then
    rsync -avz -e "ssh -i $SSH_KEY" $EXCLUDE_FLAGS "$LOCAL_DIR/" "$EC2_USER@$EC2_HOST:$RELEASE_DIR/"
else
    echo "⚠️ rsync not found, falling back to scp..."
    scp -i "$SSH_KEY" -r "$LOCAL_DIR/"* "$EC2_USER@$EC2_HOST:$RELEASE_DIR/"
fi

# Ensure the release directory has the latest timestamp to prevent accidental cleanup
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "touch $RELEASE_DIR"

# 3.5 Cache Busting (Update HTML references)
echo "✨ Applying cache busting..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
    cd "$RELEASE_DIR"
    # Find all HTML files and apply cache busting
    find . -name "*.html" -type f | while read -r html_file; do
        # Replace .css" and .js" with .css?v=TIMESTAMP" and .js?v=TIMESTAMP"
        # Also handles existing query params like .css?v=old" -> .css?v=new"
        # Use -E for extended regex to simplify syntax
        # Use # as delimiter to avoid conflict with | (alternation) in regex
        sed -E -i 's#\.(css|js)(\?v=[^"]*)?"#.\1?v='"$TIMESTAMP"'"#g' "\$html_file"
    done
    if [ -f "index.html" ]; then
        # Ensure index.html is also processed (though find should catch it)
        :
    fi
EOF

# 4. Link Shared Resources
echo "🔗 Linking shared resources..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
    # Link .env if exists
    if [ -f "$REMOTE_SERVICE_DIR/shared/.env" ]; then
        ln -sf "$REMOTE_SERVICE_DIR/shared/.env" "$RELEASE_DIR/.env"
    fi
    
    # Link logs
    if [ -d "$REMOTE_SERVICE_DIR/shared/logs" ]; then
        rm -rf "$RELEASE_DIR/logs"
        ln -sf "$REMOTE_SERVICE_DIR/shared/logs" "$RELEASE_DIR/logs"
    fi
EOF

# 5. Install Dependencies (Backend Only)
if [[ "$SERVICE" == "downloader-backend" ]]; then
    echo "🐍 Installing Python dependencies..."
    ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
        cd "$RELEASE_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
EOF
elif [[ "$SERVICE" == "converter-backend" ]]; then
    echo "📦 Installing Node.js dependencies..."
    ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
        cd "$RELEASE_DIR"
        npm install --production
EOF
fi

# 6. Switch Symlink (Atomic Deployment)
echo "🔄 Switching '$LINK_NAME' symlink..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
    ln -sfn "$RELEASE_DIR" "$TARGET_LINK"
EOF

# 7. Post-Deployment Tasks (Restart Services)
if [[ "$ENV" == "prod" ]]; then
    if [[ "$SERVICE" == "downloader-backend" ]]; then
        echo "🔄 Restarting Downloader Backend (Systemd)..."
        ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
            # Check if service exists, if not, copy it
            if [ -f "$TARGET_LINK/hqmx-backend.service" ]; then
                sudo cp "$TARGET_LINK/hqmx-backend.service" /etc/systemd/system/hqmx-downloader.service
                sudo systemctl daemon-reload
                sudo systemctl enable hqmx-downloader
            fi
            sudo systemctl restart hqmx-downloader
EOF
    elif [[ "$SERVICE" == "converter-backend" ]]; then
        echo "🔄 Restarting Converter Backend (PM2)..."
        ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
            cd "$TARGET_LINK"
            pm2 startOrRestart ecosystem.config.cjs --env production
            pm2 save
EOF
    fi
fi

# 8. Cleanup Old Releases (Keep last 5)
echo "🧹 Cleaning up old releases..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
    cd "$REMOTE_SERVICE_DIR/releases"
    ls -r | tail -n +6 | xargs -I {} rm -rf {}
EOF

echo "✅ Deployment Complete!"
echo "Deployed to: $TARGET_LINK"
