# Automated deployment script for B2B Contact Miner
$server = "root@85.198.86.237"
$password = "r0M4n0v_"
$projectPath = "C:\Users\romanov\PycharmProjects\b2b-contact-miner"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "B2B Contact Miner - Auto Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test connection
Write-Host "[1/6] Testing SSH connection..." -ForegroundColor Yellow
try {
    $testResult = ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 $server "echo 'Connection OK'" 2>&1
    if ($testResult -like "*Connection OK*") {
        Write-Host "✓ SSH connection successful!" -ForegroundColor Green
    } else {
        Write-Host "✗ SSH connection failed. Please check credentials." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ SSH test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Push latest changes to GitHub
Write-Host "[2/6] Pushing latest changes to GitHub..." -ForegroundColor Yellow
Set-Location $projectPath
git add .
git commit -m "Pre-deployment update" 2>$null || Write-Host "No changes to commit" -ForegroundColor Gray
git push
Write-Host "✓ Code pushed to GitHub" -ForegroundColor Green

Write-Host ""

# Step 3: Deploy to server
Write-Host "[3/6] Deploying to server..." -ForegroundColor Yellow
Write-Host "This will take 5-10 minutes. Please wait..." -ForegroundColor Gray
Write-Host ""

# Create deployment script on server
$deployCommands = @"
#!/bin/bash
set -e

echo 'Updating system...'
apt update -qq && apt upgrade -y -qq > /dev/null 2>&1

echo 'Installing dependencies...'
DEBIAN_FRONTEND=noninteractive apt install -y -qq python3-pip python3-venv python3-dev nginx mysql-server git curl wget supervisor > /dev/null 2>&1

echo 'Setting up application...'
mkdir -p /opt/b2b-contact-miner
cd /opt/b2b-contact-miner
git clone https://github.com/hauptmann1971/b2b-contact-miner.git . 2>/dev/null || git pull

echo 'Creating virtual environment...'
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo 'Installing Playwright browsers...'
playwright install chromium 2>&1 | tail -1
playwright install-deps 2>&1 | tail -1

echo 'Setting up MySQL database...'
mysql -u root <<MYSQL_EOF
CREATE DATABASE IF NOT EXISTS b2b_contact_miner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'b2b_user'@'localhost' IDENTIFIED BY 'b2b_password_2024';
GRANT ALL PRIVILEGES ON b2b_contact_miner.* TO 'b2b_user'@'localhost';
FLUSH PRIVILEGES;
MYSQL_EOF

echo 'Initializing database...'
python3 -c "from models.database import init_db; init_db()" 2>&1 | tail -1

echo 'Running migrations...'
python3 migrations/apply_llm_tracking_migration.py 2>&1 | tail -1 || true
python3 migrations/apply_contacts_json_migration.py 2>&1 | tail -1 || true
python3 migrations/apply_raw_search_response_migration.py 2>&1 | tail -1 || true

echo 'Configuring Nginx...'
cat > /etc/nginx/sites-available/b2b-contact-miner <<'NGINX_CONF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias /opt/b2b-contact-miner/static/;
        expires 30d;
    }
}
NGINX_CONF

ln -sf /etc/nginx/sites-available/b2b-contact-miner /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t > /dev/null 2>&1 && systemctl restart nginx

echo 'Configuring Supervisor...'
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

supervisorctl reread > /dev/null 2>&1
supervisorctl update > /dev/null 2>&1
supervisorctl restart all > /dev/null 2>&1

echo 'Setting permissions...'
chmod +x /opt/b2b-contact-miner/*.py

echo ''
echo '✅ Deployment completed successfully!'
echo ''
echo 'Web server: http://85.198.86.237/'
echo 'Health check: http://85.198.86.237/health-check'
echo ''
"@

# Save deploy script locally
$deployScriptPath = "$projectPath\remote_deploy.sh"
$deployCommands | Out-File -FilePath $deployScriptPath -Encoding ASCII

# Copy script to server
Write-Host "Uploading deployment script..." -ForegroundColor Gray
scp -o StrictHostKeyChecking=no $deployScriptPath ${server}:/tmp/deploy.sh

# Execute deployment script on server
Write-Host "Executing deployment on server (this will take 5-10 minutes)..." -ForegroundColor Gray
ssh -o StrictHostKeyChecking=no $server "bash /tmp/deploy.sh"

Write-Host "✓ Deployment completed!" -ForegroundColor Green

Write-Host ""
Write-Host "[4/6] Verifying deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if services are running
try {
    $statusCheck = ssh -o StrictHostKeyChecking=no $server "supervisorctl status" 2>&1
    Write-Host $statusCheck -ForegroundColor Gray
} catch {
    Write-Host "Could not verify service status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/6] Testing web server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://85.198.86.237/" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Web server is responding!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Web server may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[6/6] Creating post-deployment checklist..." -ForegroundColor Yellow

$checklist = @"
==========================================
✅ DEPLOYMENT COMPLETE!
==========================================

📍 Server: 85.198.86.237
🌐 Web Interface: http://85.198.86.237/
🏥 Health Check: http://85.198.86.237/health-check
📊 LLM Data: http://85.198.86.237/llm-data

📋 NEXT STEPS:

1. Update .env configuration:
   ssh root@85.198.86.237
   nano /opt/b2b-contact-miner/.env
   
   Update these values:
   - DB_USER=b2b_user
   - DB_PASSWORD=b2b_password_2024
   - DB_HOST=localhost
   - DB_NAME=b2b_contact_miner
   - Add your LLM API keys if needed

2. Restart services after config update:
   supervisorctl restart all

3. Start the pipeline manually when ready:
   cd /opt/b2b-contact-miner
   source venv/bin/activate
   python main.py

4. Monitor logs:
   supervisorctl status
   tail -f /opt/b2b-contact-miner/logs/web_out.log

🔧 USEFUL COMMANDS:

   # Service management
   supervisorctl status              # Check all services
   supervisorctl restart all         # Restart all services
   supervisorctl restart b2b-web     # Restart web server only
   
   # View logs
   tail -f /opt/b2b-contact-miner/logs/web_out.log
   tail -f /opt/b2b-contact-miner/logs/web_err.log
   
   # Database access
   mysql -u b2b_user -p b2b_contact_miner
   
   # Run pipeline
   cd /opt/b2b-contact-miner
   source venv/bin/activate
   python main.py

==========================================
"@

Write-Host $checklist -ForegroundColor Cyan

# Cleanup
Remove-Item $deployScriptPath -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Deployment script finished!" -ForegroundColor Green
