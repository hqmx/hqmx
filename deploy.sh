#!/bin/bash

# HQMX Unified Deployment Wrapper
# Usage: ./deploy.sh <service_name> [env]
# Example: ./deploy.sh converter
# Example: ./deploy.sh main prod

SERVICE=$1
ENV=${2:-prod}

if [ -z "$SERVICE" ]; then
    echo "❌ Error: Service name is required."
    echo "Usage: ./deploy.sh <service_name> [env]"
    echo "Available services: main, converter, downloader, generator, calculator"
    exit 1
fi

# Execute the modular deployment script
./scripts/deploy-modular.sh --service="$SERVICE" --env="$ENV"
