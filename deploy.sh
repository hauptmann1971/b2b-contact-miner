#!/bin/bash
# Deployment script for B2B Contact Miner on Ubuntu

set -e  # Exit on error

echo "=========================================="
echo "B2B Contact Miner - Server Setup"
echo "=========================================="

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    mysql-server \
    git \
    curl \
    wget \
    supervisor \
    redis-server

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/b2b-contact-miner
cd /opt/b2b-contact-miner

# Clone repository
echo "📥 Cloning repository..."
git clone https://github.com/hauptmann1971/b2b-contact-miner.git .

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# Create .env file from template
echo "⚙️  Creating .env configuration..."
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || echo "No .env.example found, please configure manually"
fi

# Create necessary directories
echo "📂 Creating directories..."
mkdir -p logs
mkdir -p migrations

# Setup MySQL database
echo "🗄️  Setting up MySQL database..."
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS b2b_contact_miner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'b2b_user'@'localhost' IDENTIFIED BY 'b2b_password_2024';
GRANT ALL PRIVILEGES ON b2b_contact_miner.* TO 'b2b_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Initialize database tables
echo "📊 Initializing database tables..."
python3 -c "
import sys
sys.path.insert(0, '/opt/b2b-contact-miner')
from models.database import init_db
init_db()
print('Database tables created successfully')
"

# Run migrations
echo "🔄 Running database migrations..."
python3 migrations/apply_llm_tracking_migration.py || echo "LLM tracking migration skipped (may already exist)"
python3 migrations/apply_contacts_json_migration.py || echo "Contacts JSON migration skipped (may already exist)"
python3 migrations/apply_raw_search_response_migration.py || echo "Raw search response migration skipped (may already exist)"

# Configure Nginx
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/b2b-contact-miner <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /opt/b2b-contact-miner/static/;
        expires 30d;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/b2b-contact-miner /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Configure Supervisor for process management
echo "🔄 Configuring Supervisor..."

# Flask web server
cat > /etc/supervisor/conf.d/b2b-web.conf <<'EOF'
[program:b2b-web]
command=/opt/b2b-contact-miner/venv/bin/python web_server.py
directory=/opt/b2b-contact-miner
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/opt/b2b-contact-miner/logs/web_err.log
stdout_logfile=/opt/b2b-contact-miner/logs/web_out.log
environment=PYTHONPATH="/opt/b2b-contact-miner"
EOF

# FastAPI monitoring service
cat > /etc/supervisor/conf.d/b2b-monitoring.conf <<'EOF'
[program:b2b-monitoring]
command=/opt/b2b-contact-miner/venv/bin/python monitoring/healthcheck.py
directory=/opt/b2b-contact-miner
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/opt/b2b-contact-miner/logs/monitoring_err.log
stdout_logfile=/opt/b2b-contact-miner/logs/monitoring_out.log
environment=PYTHONPATH="/opt/b2b-contact-miner"
EOF

# Restart Supervisor
supervisorctl reread
supervisorctl update
supervisorctl restart all

# Set proper permissions
echo "🔒 Setting permissions..."
chown -R root:root /opt/b2b-contact-miner
chmod -R 755 /opt/b2b-contact-miner
chmod +x /opt/b2b-contact-miner/*.py

# Create systemd service for pipeline (optional, run manually when needed)
cat > /etc/systemd/system/b2b-pipeline.service <<'EOF'
[Unit]
Description=B2B Contact Miner Pipeline
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/b2b-contact-miner
ExecStart=/opt/b2b-contact-miner/venv/bin/python main.py
Restart=on-failure
RestartSec=10
Environment=PYTHONPATH=/opt/b2b-contact-miner

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Display status
echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - Flask Web Server: http://85.198.86.237/"
echo "  - Monitoring API: http://85.198.86.237:8000/health"
echo "  - Health Check: http://85.198.86.237/health-check"
echo ""
echo "Supervisor commands:"
echo "  supervisorctl status          # Check service status"
echo "  supervisorctl restart all     # Restart all services"
echo "  supervisorctl logs b2b-web    # View web server logs"
echo ""
echo "Pipeline execution:"
echo "  systemctl start b2b-pipeline  # Start pipeline manually"
echo "  systemctl status b2b-pipeline # Check pipeline status"
echo ""
echo "Important files:"
echo "  - Config: /opt/b2b-contact-miner/.env"
echo "  - Logs: /opt/b2b-contact-miner/logs/"
echo "  - Nginx: /etc/nginx/sites-available/b2b-contact-miner"
echo ""
echo "⚠️  IMPORTANT: Update .env with your actual database credentials and API keys!"
echo "=========================================="
