#!/bin/bash

# GHOST CMD - Dashboard Installer
# Run once on main server

set -e

echo "🚀 GHOST CMD Dashboard Installer"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo bash install.sh"
    exit 1
fi

# ==========================================
# 1. System Update
# ==========================================
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv git curl wget

# ==========================================
# 2. Setup Python Environment
# ==========================================
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# ==========================================
# 3. Setup Data Directories
# ==========================================
echo "📁 Creating data directories..."
mkdir -p data/slots
mkdir -p data/logs
mkdir -p static

# ==========================================
# 4. Cloudflare Tunnel Setup
# ==========================================
echo "🌐 Setting up Cloudflare Tunnel..."

if ! command -v cloudflared &> /dev/null; then
    echo "   Downloading cloudflared..."
    wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
    chmod +x cloudflared
    mv cloudflared /usr/local/bin/
fi

# Create tunnel (User must auth manually)
echo "   Authenticating with Cloudflare..."
echo "   (A browser window should open - login with your Cloudflare account)"
cloudflared tunnel login

read -p "   Enter tunnel name (e.g., ghost-dashboard): " TUNNEL_NAME

# Create tunnel config
TUNNEL_ID=$(cloudflared tunnel create $TUNNEL_NAME | grep -oP '(?<=\()[a-f0-9\-]+(?=\))' | head -1)

cat > config.yaml <<EOF
tunnel: $TUNNEL_ID
credentials-file: ~/.cloudflare-warp/cert.pem

ingress:
  - hostname: dashboard.jujulefek.qzz.io
    service: http://localhost:5000
  - service: http_status:404
EOF

echo "   Tunnel created: $TUNNEL_ID"
echo "   Config saved to config.yaml"

# ==========================================
# 5. Create Systemd Service
# ==========================================
echo "⚙️  Creating systemd service..."

cat > /etc/systemd/system/ghost-dashboard.service <<EOF
[Unit]
Description=GHOST CMD Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ghost-dashboard.service

# ==========================================
# 6. Create Tunnel Service
# ==========================================
echo "🔗 Creating tunnel service..."

cat > /etc/systemd/system/ghost-tunnel.service <<EOF
[Unit]
Description=GHOST CMD Tunnel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/cloudflared tunnel --config config.yaml run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ghost-tunnel.service

# ==========================================
# 7. Start Services
# ==========================================
echo "🚀 Starting services..."
systemctl start ghost-dashboard.service
systemctl start ghost-tunnel.service

sleep 2

echo ""
echo "✅ Installation Complete!"
echo "=================================="
echo "📊 Dashboard: http://localhost:5000"
echo "🌐 Public URL: https://dashboard.jujulefek.qzz.io"
echo "📝 Auth Key: GHOST_SECRET_2026"
echo ""
echo "🔧 Manage services:"
echo "   systemctl status ghost-dashboard"
echo "   systemctl status ghost-tunnel"
echo "   systemctl restart ghost-dashboard"
echo ""
echo "📋 Logs:"
echo "   journalctl -u ghost-dashboard -f"
echo "   journalctl -u ghost-tunnel -f"
echo ""
