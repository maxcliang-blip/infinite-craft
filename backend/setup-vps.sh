#!/bin/bash
set -e

echo "Installing Docker..."
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

echo "Installing docker compose plugin..."
apt-get update && apt-get install -y docker-compose-plugin

echo "Done! Docker is ready."
docker --version
docker compose version
