#!/bin/bash
set -e

VPS_USER="${VPS_USER:-root}"
VPS_HOST="${VPS_HOST:-your-vps-ip}"
REMOTE_PATH="/opt/infinite-craft"

echo "=== Deploying backend to $VPS_HOST ==="

echo "Transferring files..."
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.env' ./ "$VPS_USER@$VPS_HOST:$REMOTE_PATH/backend/"

echo "Restarting service..."
ssh "$VPS_USER@$VPS_HOST" "systemctl restart infinite-craft"

echo "Deploy complete! Backend at http://$VPS_HOST:8000"
