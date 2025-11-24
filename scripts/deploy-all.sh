#!/bin/bash

# HQMX All-in-One Parallel Deployment Script
# Usage: ./deploy-all.sh [--env=<prod|dev>] [--services="service1 service2..."]

set -e

# Configuration
ENV="dev" # Default to dev for safety
SERVICES="main downloader calculator generator converter" # Default services

# Parse Arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --env=*) ENV="${1#*=}"; shift ;;
        --services=*) SERVICES="${1#*=}"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================"
echo -e "${BLUE}🚀 HQMX Parallel Deployment${NC}"
echo "============================================"
echo -e "Environment: ${YELLOW}$ENV${NC}"
echo -e "Services: ${YELLOW}$SERVICES${NC}"
echo "============================================"
echo ""

# Deployment function
deploy_service() {
    local service=$1
    local env=$2
    
    echo -e "${BLUE}[START]${NC} Deploying ${YELLOW}$service${NC} to ${YELLOW}$env${NC}..."
    
    if ./scripts/deploy-modular.sh --service="$service" --env="$env" > "logs/deploy-$service-$env.log" 2>&1; then
        echo -e "${GREEN}[SUCCESS]${NC} $service deployed successfully!"
        return 0
    else
        echo -e "${RED}[FAILED]${NC} $service deployment failed! Check logs/deploy-$service-$env.log"
        return 1
    fi
}

# Create logs directory if not exists
mkdir -p logs

# Array to store PIDs
declare -a pids
declare -a service_names

# Start all deployments in parallel
for service in $SERVICES; do
    deploy_service "$service" "$ENV" &
    pids+=($!)
    service_names+=("$service")
done

# Wait for all deployments to complete
echo ""
echo -e "${BLUE}⏳ Waiting for all deployments to complete...${NC}"
echo ""

failed=0
for i in "${!pids[@]}"; do
    pid=${pids[$i]}
    service=${service_names[$i]}
    
    if wait $pid; then
        echo -e "${GREEN}✓${NC} $service"
    else
        echo -e "${RED}✗${NC} $service"
        ((failed++))
    fi
done

echo ""
echo "============================================"
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ All deployments completed successfully!${NC}"
    echo "============================================"
    exit 0
else
    echo -e "${RED}❌ $failed deployment(s) failed!${NC}"
    echo "Check individual log files in logs/ directory"
    echo "============================================"
    exit 1
fi
