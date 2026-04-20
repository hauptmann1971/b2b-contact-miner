# 🚀 B2B Contact Miner - Deployment Guide for Ubuntu Server

## Server Information
- **Host**: 85.198.86.237
- **User**: root
- **Password**: r0M4n0v_

---

## Quick Start (Automated)

### Option 1: Using the deployment script

1. Connect to server:
```bash
ssh root@85.198.86.237
# Password: r0M4n0v_
```

2. Run the automated deployment script:
```bash
cd /tmp
wget https://raw.githubusercontent.com/hauptmann1971/b2b-contact-miner/main/deploy.sh
chmod +x deploy.sh
bash deploy.sh
```

The script will automatically:
- ✅ Install all dependencies (Python, MySQL, Nginx, Supervisor)
- ✅ Clone the repository
- ✅ Setup virtual environment
- ✅ Install Python packages
- ✅ Configure MySQL database
- ✅ Initialize database tables
- ✅ Run migrations
- ✅ Configure Nginx as reverse proxy
- ✅ Setup Supervisor for process management
- ✅ Start all services

---

## Manual Installation (Step-by-Step)

If you prefer manual installation or the script fails:

### Step 1: Update System
```bash
apt update && apt upgrade -y
```

### Step 2: Install Dependencies
```bash
apt install -y python3-pip python3-venv python3-dev nginx mysql-server git curl wget supervisor
```

### Step 3: Clone Repository
```bash
mkdir -p /opt/b2b-contact-miner
cd /opt/b2b-contact-miner
git clone https://github.com/hauptmann1971/b2b-contact-miner.git .
```

### Step 4: Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Install Playwright Browsers
```bash
playwright install chromium
playwright install-deps
```

### Step 6: Setup MySQL Database
```bash
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS b2b_contact_miner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'b2b_user'@'localhost' IDENTIFIED BY 'b2b_password_2024';
GRANT ALL PRIVILEGES ON b2b_contact_miner.* TO 'b2b_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF
```

### Step 7: Initialize Database
```bash
cd /opt/b2b-contact-miner
source venv/bin/activate
python3 -c "from models.database import init_db; init_db()"
```

### Step 8: Run Migrations
```bash
python3 migrations/apply_llm_tracking_migration.py || echo "Migration may already exist"
python3 migrations/apply_contacts_json_migration.py || echo "Migration may already exist"
python3 migrations/apply_raw_search_response_migration.py || echo "Migration may already exist"
```

### Step 9: Configure Nginx
```bash
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
    
    location /static/ {
        alias /opt/b2b-contact-miner/static/;
        expires 30d;
    }
}
EOF

ln -sf /etc/nginx/sites-available/b2b-contact-miner /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

### Step 10: Configure Supervisor
```bash
mkdir -p /opt/b2b-contact-miner/logs

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

supervisorctl reread
supervisorctl update
supervisorctl restart all
```

### Step 11: Set Permissions
```bash
chmod +x /opt/b2b-contact-miner/*.py
chown -R root:root /opt/b2b-contact-miner
```

---

## Post-Deployment Configuration

### Update .env File
```bash
nano /opt/b2b-contact-miner/.env
```

Update these values:
```env
DB_USER=b2b_user
DB_PASSWORD=b2b_password_2024
DB_HOST=localhost
DB_NAME=b2b_contact_miner

# Add your API keys if needed
YANDEX_IAM_TOKEN=your_token_here
YANDEX_FOLDER_ID=your_folder_id_here
GIGACHAT_CLIENT_ID=your_client_id
GIGACHAT_CLIENT_SECRET=your_secret
```

Save and exit (Ctrl+X, Y, Enter)

### Restart Services
```bash
supervisorctl restart all
```

---

## Access Your Application

- **Web Interface**: http://85.198.86.237/
- **Health Check**: http://85.198.86.237/health-check
- **LLM Data Viewer**: http://85.198.86.237/llm-data
- **API Docs**: http://85.198.86.237:8000/docs (if monitoring is running)

---

## Useful Commands

### Service Management
```bash
# Check status of all services
supervisorctl status

# Restart all services
supervisorctl restart all

# Restart only web server
supervisorctl restart b2b-web

# View web server logs
tail -f /opt/b2b-contact-miner/logs/web_out.log
tail -f /opt/b2b-contact-miner/logs/web_err.log
```

### Database Access
```bash
# Connect to MySQL
mysql -u b2b_user -p b2b_contact_miner
# Password: b2b_password_2024

# Show tables
SHOW TABLES;

# Exit
EXIT;
```

### Run Pipeline
```bash
cd /opt/b2b-contact-miner
source venv/bin/activate
python main.py
```

### Monitor System
```bash
# Check Nginx status
systemctl status nginx

# Check MySQL status
systemctl status mysql

# Check Supervisor status
supervisorctl status

# View system resources
htop
df -h
free -m
```

---

## Troubleshooting

### Web server not starting
```bash
# Check logs
tail -100 /opt/b2b-contact-miner/logs/web_err.log

# Check if port 5000 is in use
netstat -tlnp | grep 5000

# Restart service
supervisorctl restart b2b-web
```

### Database connection errors
```bash
# Check MySQL is running
systemctl status mysql

# Test connection
mysql -u b2b_user -p'b2b_password_2024' b2b_contact_miner -e "SELECT 1;"
```

### Nginx errors
```bash
# Test configuration
nginx -t

# Check error log
tail -50 /var/log/nginx/error.log

# Restart Nginx
systemctl restart nginx
```

### Permission issues
```bash
# Fix permissions
chown -R root:root /opt/b2b-contact-miner
chmod -R 755 /opt/b2b-contact-miner
chmod +x /opt/b2b-contact-miner/*.py
```

---

## Security Recommendations

1. **Change default passwords** in .env file
2. **Setup firewall**:
   ```bash
   ufw allow 22/tcp   # SSH
   ufw allow 80/tcp   # HTTP
   ufw enable
   ```

3. **Enable HTTPS** with Let's Encrypt:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d your-domain.com
   ```

4. **Regular updates**:
   ```bash
   apt update && apt upgrade -y
   cd /opt/b2b-contact-miner
   git pull
   source venv/bin/activate
   pip install -r requirements.txt
   supervisorctl restart all
   ```

---

## Support

For issues or questions:
- Check logs: `/opt/b2b-contact-miner/logs/`
- GitHub: https://github.com/hauptmann1971/b2b-contact-miner
- Documentation: See README.md in project root
