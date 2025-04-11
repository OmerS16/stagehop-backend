#!/bin/bash

KEY_PATH=./LightsailDefaultKey-eu-central-1.pem
REMOTE_USER=ubuntu
REMOTE_IP=18.196.176.140
REMOTE_DIR=/home/ubuntu/stagehop-backend

echo "🚀 Connecting to $REMOTE_IP and deploying FastAPI..."

ssh -i $KEY_PATH $REMOTE_USER@$REMOTE_IP << "EOF"
set -e

cd /home/ubuntu/stagehop-backend

echo "📥 Pulling latest code..."
git pull origin main

cd backend

# Create venv if it doesn't exist
if [ ! -d "api_env" ]; then
    echo "🐍 Creating backend virtual environment..."
    python3 -m venv api_env
fi

echo "📦 Installing backend requirements..."
api_env/bin/pip install -r requirements.txt

echo "🔄 Restarting FastAPI service..."
sudo systemctl daemon-reload
sudo systemctl restart fastapi

echo "✅ FastAPI status:"
sudo systemctl status fastapi | head -n 10
EOF

echo "✅ Deployment complete!"
