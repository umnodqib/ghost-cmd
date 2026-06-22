#!/bin/bash
# GHOST CMD - Agent Installer
# Run on each agent server
set -e

echo "🚀 GHOST CMD Agent Installer"
echo "============================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash install-agent.sh"
    exit 1
fi

# ==========================================
# 1. Get Dashboard URL
# ==========================================
read -p "📊 Enter Dashboard URL (e.g., https://dashboard.jujulefek.qzz.io): " DASHBOARD_URL
if [ -z "$DASHBOARD_URL" ]; then
    echo "❌ Dashboard URL cannot be empty"
    exit 1
fi

# ==========================================
# 2. System Update & Dependencies (XVFB Fixed)
# ==========================================
echo "📦 Updating system packages and installing dependencies..."
apt-get update && apt-get upgrade -y

apt-get install -y \
    python3 python3-pip python3-venv git curl wget \
    xvfb x11-utils libx11-6 libxcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libxtst6 libnss3 libasound2 libatk1.0-0 \
    libatk-bridge2.0-0 libgtk-3-0 libgbm1 libxshmfence1 \
    fonts-liberation libappindicator3-1 libdbusmenu-gtk4

echo "✅ Core dependencies & XVFB installed"

# ==========================================
# 3. Install Google Chrome
# ==========================================
echo "🌐 Installing Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    echo "📦 Installing Chrome via official repository..."
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update
    apt-get install -y google-chrome-stable
    echo "✅ Google Chrome installed successfully"
else
    echo "✅ Google Chrome already installed"
fi

# ==========================================
# 4. Setup Python Environment
# ==========================================
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ==========================================
# 5. Create directories
# ==========================================
echo "📁 Creating directories..."
mkdir -p chrome_profiles
mkdir -p logs

# ==========================================
# 6. Create environment file
# ==========================================
echo "⚙️ Creating .env configuration..."
cat > .env <<EOF
DASHBOARD_URL=$DASHBOARD_URL
AUTH_KEY=GHOST_SECRET_2026
EOF

# ==========================================
# 7. Create Agent Systemd Service
# ==========================================
echo "⚙️ Creating ghost-agent systemd service..."

cat > /etc/systemd/system/ghost-agent.service <<EOF
[Unit]
Description=GHOST CMD Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/venv/bin/python3 agent.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=:99
XDG_RUNTIME_DIR=/run/user/0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ghost-agent.service

# ==========================================
# 8. Start Service
# ==========================================
echo "🚀 Starting agent service..."
systemctl start ghost-agent.service

sleep 3

# ==========================================
# 9. Final Message
# ==========================================
echo ""
echo "✅ Agent Installation Complete!"
echo "============================"
echo "📊 Dashboard URL : $DASHBOARD_URL"
echo "🚀 Agent running on http://localhost:7860"
echo ""
echo "🔧 Service Management:"
echo "   systemctl status ghost-agent"
echo "   systemctl restart ghost-agent"
echo "   systemctl stop ghost-agent"
echo ""
echo "📋 Logs:"
echo "   journalctl -u ghost-agent -f"
echo ""
echo "🎉 Agent siap mendaftar ke Dashboard secara otomatis."
echo ""

# Show current status
echo "Current service status:"
systemctl status ghost-agent --no-pager -l
