#!/bin/bash
set -e

VPS_USER="${VPS_USER:-root}"
VPS_HOST="${VPS_HOST:-your-vps-ip}"
REMOTE_PATH="/opt/infinite-craft"

echo "=== Deploying to $VPS_HOST ==="

ssh "$VPS_USER@$VPS_HOST" bash -s << 'REMOTE'
set -e

echo "Setting up directory..."
mkdir -p /opt/infinite-craft
cd /opt/infinite-craft

echo "Pulling latest code..."
if [ -d ".git" ]; then
  git pull origin main
else
  git clone https://github.com/maxcliang-blip/infinite-craft.git .
fi

cd backend

echo "Building and starting container..."
docker compose down --remove-orphans || true
docker compose up -d --build

echo "Done! Backend at http://$(hostname -i):8000"
REMOTE

echo "Deploy complete!"
