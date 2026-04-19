#!/bin/bash
# setup.sh - AuditorSEC MVP on clean Ubuntu 22.04
set -e

echo "== AuditorSEC Setup =="

# 1. Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in."
else
    echo "Docker already installed."
fi

# 2. Clone repo (skip if already in repo dir)
if [ ! -f "main.py" ]; then
    echo "Cloning auditorsec repo..."
    git clone https://github.com/romanchaa997/auditorsec.git
    cd auditorsec
fi

# 3. Setup env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "Edit .env - add your OPENAI_API_KEY and MINIO_SECRET_KEY"
    read -p "Press Enter after editing .env..."
fi

# 4. Start stack
echo "Starting AuditorSEC stack..."
docker compose up -d

# 5. Health check
echo "Waiting for API to start..."
sleep 5
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "AuditorSEC MVP is running!"
echo "  API:    http://localhost:8000"
echo "  Docs:   http://localhost:8000/docs"
echo "  MinIO:  http://localhost:9001"
echo ""
echo "Test audit:"
echo 'curl -X POST http://localhost:8000/api/v1/audit -H "Content-Type: application/json" -d \'{\'\''"project_name":"Test","log_text":"Private key in .env","audit_type":"key_mgmt"}\'\'''  
