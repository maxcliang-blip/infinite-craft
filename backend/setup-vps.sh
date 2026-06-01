#!/bin/bash
set -e

echo "=== Setting up backend on VPS ==="

echo "Installing Python..."
if command -v apt-get &> /dev/null; then
  apt-get update && apt-get install -y python3 python3-pip python3-venv curl
elif command -v yum &> /dev/null; then
  yum install -y python3 python3-pip curl
fi

echo "Setting up app..."
mkdir -p /opt/infinite-craft/backend
cd /opt/infinite-craft/backend

echo "Creating venv..."
python3 -m venv .venv
source .venv/bin/activate

if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  pip install fastapi uvicorn httpx python-dotenv pydantic
fi

echo "Setting up systemd service..."
cat > /etc/systemd/system/infinite-craft.service << 'EOF'
[Unit]
Description=Infinite Craft Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/infinite-craft/backend
Environment=PATH=/opt/infinite-craft/backend/.venv/bin:/usr/bin
ExecStart=/opt/infinite-craft/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable infinite-craft
systemctl restart infinite-craft

echo "Done! Backend running at http://$(hostname -I | awk '{print $1}'):8000"
systemctl status infinite-craft --no-pager
