#!/bin/bash
# Deployment script for B2B Contact Miner on Ubuntu
set -e

echo "=========================================="
echo "B2B Contact Miner - Server Setup"
echo "=========================================="

# Update system
echo "Updating system..."
apt update -y && apt upgrade -y

# Install dependencies
echo "Installing dependencies..."
DEBIAN_FRONTEND=noninteractive apt install -y python3-pip python3-venv python3-dev nginx mysql-server git curl wget supervisor

# Create application directory
echo "Setting up application..."
mkdir -p /opt/b2b-contact-miner
cd /opt/b2b-contact-miner

# Clone repository
if [ -d ".git" ]; then
    echo "Pulling latest changes..."
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/hauptmann1971/b2b-contact-miner.git .
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# Setup MySQL database
echo "Setting up MySQL database..."
mysql -u root <<MYSQL_EOF
CREATE DATABASE IF NOT EXISTS b2b_contact_miner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'b2b_user'@'localhost' IDENTIFIED BY 'b2b_password_2024';
GRANT ALL PRIVILEGES ON b2b_contact_miner.* TO 'b2b_user'@'localhost';
FLUSH PRIVILEGES;
MYSQL_EOF

# Initialize database
echo "Initializing database..."
python3 -c "from models.database import init_db; init_db()"

# Run migrations
echo "Running migrations..."
python3 migrations/apply_llm_tracking_migration.py || echo "LLM tracking migration skipped (may already exist)"
python3 migrations/apply_contacts_json_migration.py || echo "Contacts JSON migration skipped (may already exist)"
python3 migrations/apply_raw_search_response_migration.py || echo "Raw search response migration skipped (may already exist)"

# Configure Nginx
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/b2b-contact-miner <<'NGINX_CONF'
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
    
    location /static/ {
        alias /opt/b2b-contact-miner/static/;
        expires 30d;
    }
}
NGINX_CONF

ln -sf /etc/nginx/sites-available/b2b-contact-miner /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Configure Supervisor
echo "Configuring Supervisor..."
mkdir -p /opt/b2b-contact-miner/logs

cat > /etc/supervisor/conf.d/b2b-web.conf <<'SUPERVISOR_CONF'
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
SUPERVISOR_CONF

supervisorctl reread
supervisorctl update
supervisorctl restart all

# Set permissions
echo "Setting permissions..."
chmod +x /opt/b2b-contact-miner/*.py

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Web server: http://85.198.86.237/"
echo "Health check: http://85.198.86.237/health-check"
echo ""
echo "Next steps:"
echo "1. Update .env file: nano /opt/b2b-contact-miner/.env"
echo "2. Restart services: supervisorctl restart all"
echo "3. Run pipeline: cd /opt/b2b-contact-miner && source venv/bin/activate && python main.py"
echo "=========================================="