#!/bin/bash

# Redis Installation Script for HQMX API Rate Limiting
# Purpose: Install and configure Redis for IP-based rate limiting (28 requests/day)

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Installing Redis for API Rate Limiting               ║"
echo "╚════════════════════════════════════════════════════════╝"

# 1. Update package list
echo ""
echo "[1/5] Updating package list..."
sudo apt-get update

# 2. Install Redis
echo ""
echo "[2/5] Installing Redis Server..."
sudo apt-get install -y redis-server

# 3. Configure Redis
echo ""
echo "[3/5] Configuring Redis..."
sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sudo sed -i 's/^bind 127.0.0.1 ::1/bind 127.0.0.1/' /etc/redis/redis.conf

# Set maxmemory policy (LRU eviction)
if ! grep -q "^maxmemory" /etc/redis/redis.conf; then
    echo "maxmemory 256mb" | sudo tee -a /etc/redis/redis.conf
fi
if ! grep -q "^maxmemory-policy" /etc/redis/redis.conf; then
    echo "maxmemory-policy allkeys-lru" | sudo tee -a /etc/redis/redis.conf
fi

# 4. Enable and start Redis
echo ""
echo "[4/5] Starting Redis service..."
sudo systemctl enable redis-server
sudo systemctl restart redis-server

# 5. Verify installation
echo ""
echo "[5/5] Verifying Redis installation..."
sleep 2

if sudo systemctl is-active --quiet redis-server; then
    echo "✅ Redis is running"
else
    echo "❌ Redis failed to start"
    sudo systemctl status redis-server
    exit 1
fi

# Test Redis connection
if redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis connection test: PASSED"
else
    echo "❌ Redis connection test: FAILED"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Redis Installation Complete!                          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Redis Status:"
sudo systemctl status redis-server --no-pager | head -n 10
echo ""
echo "Redis Info:"
redis-cli info | grep -E "redis_version|connected_clients|used_memory_human"
