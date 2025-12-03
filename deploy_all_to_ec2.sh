#!/bin/bash
# Wrapper script for backward compatibility and ease of use
# Deploys all services to PRODUCTION environment

echo "🚀 Starting Unified Production Deployment..."
./scripts/deploy-all.sh --env=prod
