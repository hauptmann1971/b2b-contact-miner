# PowerShell script to deploy B2B Contact Miner to Ubuntu server

$server = "root@85.198.86.237"
$password = "r0M4n0v_"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "B2B Contact Miner - Remote Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# First, copy the deploy script to server
Write-Host "📤 Copying deployment script to server..." -ForegroundColor Yellow
$deployScriptPath = "C:\Users\romanov\PycharmProjects\b2b-contact-miner\deploy.sh"

# Use plink (PuTTY) or manual SSH connection
Write-Host ""
Write-Host "⚠️  IMPORTANT: Since sshpass is not available on Windows," -ForegroundColor Red
Write-Host "   please follow these steps manually:" -ForegroundColor Red
Write-Host ""
Write-Host "1. Connect to server:" -ForegroundColor Green
Write-Host "   ssh root@85.198.86.237" -ForegroundColor White
Write-Host "   Password: r0M4n0v_" -ForegroundColor White
Write-Host ""
Write-Host "2. On the server, run these commands:" -ForegroundColor Green
Write-Host ""
Write-Host "# Update system and install dependencies" -ForegroundColor Gray
Write-Host "apt update && apt upgrade -y" -ForegroundColor White
Write-Host "apt install -y python3-pip python3-venv python3-dev nginx mysql-server git curl wget supervisor" -ForegroundColor White
Write-Host ""
Write-Host "# Clone repository" -ForegroundColor Gray
Write-Host "mkdir -p /opt/b2b-contact-miner" -ForegroundColor White
Write-Host "cd /opt/b2b-contact-miner" -ForegroundColor White
Write-Host "git clone https://github.com/hauptmann1971/b2b-contact-miner.git ." -ForegroundColor White
Write-Host ""
Write-Host "# Setup Python environment" -ForegroundColor Gray
Write-Host "python3 -m venv venv" -ForegroundColor White
Write-Host "source venv/bin/activate" -ForegroundColor White
Write-Host "pip install --upgrade pip" -ForegroundColor White
Write-Host "pip install -r requirements.txt" -ForegroundColor White
Write-Host ""
Write-Host "# Install Playwright" -ForegroundColor Gray
Write-Host "playwright install chromium" -ForegroundColor White
Write-Host "playwright install-deps" -ForegroundColor White
Write-Host ""
Write-Host "# Setup MySQL database" -ForegroundColor Gray
Write-Host "mysql -u root <<EOF" -ForegroundColor White
Write-Host "CREATE DATABASE IF NOT EXISTS b2b_contact_miner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" -ForegroundColor White
Write-Host "CREATE USER IF NOT EXISTS 'b2b_user'@'localhost' IDENTIFIED BY 'b2b_password_2024';" -ForegroundColor White
Write-Host "GRANT ALL PRIVILEGES ON b2b_contact_miner.* TO 'b2b_user'@'localhost';" -ForegroundColor White
Write-Host "FLUSH PRIVILEGES;" -ForegroundColor White
Write-Host "EOF" -ForegroundColor White
Write-Host ""
Write-Host "# Initialize database" -ForegroundColor Gray
Write-Host "python3 -c \"from models.database import init_db; init_db()\"" -ForegroundColor White
Write-Host ""
Write-Host "# Run migrations" -ForegroundColor Gray
Write-Host "python3 migrations/apply_llm_tracking_migration.py || true" -ForegroundColor White
Write-Host "python3 migrations/apply_contacts_json_migration.py || true" -ForegroundColor White
Write-Host "python3 migrations/apply_raw_search_response_migration.py || true" -ForegroundColor White
Write-Host ""
Write-Host "# Configure Nginx" -ForegroundColor Gray
Write-Host "cat > /etc/nginx/sites-available/b2b-contact-miner <<'NGINX_EOF'" -ForegroundColor White
Write-Host "server {" -ForegroundColor White
Write-Host "    listen 80;" -ForegroundColor White
Write-Host "    server_name _;" -ForegroundColor White
Write-Host "    location / {" -ForegroundColor White
Write-Host "        proxy_pass http://127.0.0.1:5000;" -ForegroundColor White
Write-Host "        proxy_set_header Host `$host;" -ForegroundColor White
Write-Host "        proxy_set_header X-Real-IP `$remote_addr;" -ForegroundColor White
Write-Host "    }" -ForegroundColor White
Write-Host "}" -ForegroundColor White
Write-Host "NGINX_EOF" -ForegroundColor White
Write-Host ""
Write-Host "ln -sf /etc/nginx/sites-available/b2b-contact-miner /etc/nginx/sites-enabled/" -ForegroundColor White
Write-Host "rm -f /etc/nginx/sites-enabled/default" -ForegroundColor White
Write-Host "nginx -t && systemctl restart nginx" -ForegroundColor White
Write-Host ""
Write-Host "# Configure Supervisor for web server" -ForegroundColor Gray
Write-Host "cat > /etc/supervisor/conf.d/b2b-web.conf <<'SUPERVISOR_EOF'" -ForegroundColor White
Write-Host "[program:b2b-web]" -ForegroundColor White
Write-Host "command=/opt/b2b-contact-miner/venv/bin/python web_server.py" -ForegroundColor White
Write-Host "directory=/opt/b2b-contact-miner" -ForegroundColor White
Write-Host "user=root" -ForegroundColor White
Write-Host "autostart=true" -ForegroundColor White
Write-Host "autorestart=true" -ForegroundColor White
Write-Host "stderr_logfile=/opt/b2b-contact-miner/logs/web_err.log" -ForegroundColor White
Write-Host "stdout_logfile=/opt/b2b-contact-miner/logs/web_out.log" -ForegroundColor White
Write-Host "SUPERVISOR_EOF" -ForegroundColor White
Write-Host ""
Write-Host "mkdir -p /opt/b2b-contact-miner/logs" -ForegroundColor White
Write-Host "supervisorctl reread" -ForegroundColor White
Write-Host "supervisorctl update" -ForegroundColor White
Write-Host "supervisorctl restart all" -ForegroundColor White
Write-Host ""
Write-Host "# Set permissions" -ForegroundColor Gray
Write-Host "chmod +x /opt/b2b-contact-miner/*.py" -ForegroundColor White
Write-Host ""
Write-Host "3. Update .env file with your credentials:" -ForegroundColor Green
Write-Host "   nano /opt/b2b-contact-miner/.env" -ForegroundColor White
Write-Host ""
Write-Host "4. Restart services:" -ForegroundColor Green
Write-Host "   supervisorctl restart all" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "After setup, access your app at:" -ForegroundColor Cyan
Write-Host "http://85.198.86.237/" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
