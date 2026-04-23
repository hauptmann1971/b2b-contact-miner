# Nginx Configuration for B2B Contact Miner

## Overview

Nginx is configured as a reverse proxy to provide secure external access to the Flask web server.

## Configuration Details

### Server Setup
- **Public URL**: http://85.198.86.237
- **Internal Flask**: http://127.0.0.1:5000 (localhost only)
- **Nginx Role**: Reverse proxy with security headers

### Configuration File
- **Location**: `/etc/nginx/sites-available/b2b-contact-miner`
- **Symlink**: `/etc/nginx/sites-enabled/b2b-contact-miner`
- **Template**: `deploy/nginx-b2b.conf` (in project repo)

## Features

### ✅ Security Headers
- X-Frame-Options: SAMEORIGIN (prevent clickjacking)
- X-Content-Type-Options: nosniff (prevent MIME sniffing)
- X-XSS-Protection: 1; mode=block (XSS filter)

### ✅ Proxy Settings
- Proper header forwarding (Host, X-Real-IP, X-Forwarded-For)
- WebSocket support ready
- Connection timeouts: 60s

### ✅ Performance
- Static file caching (30 days)
- Access logging for monitoring
- Hidden files denied

### ✅ Health Check
- Endpoint: http://85.198.86.237/health
- No logging for health checks (reduces log noise)

## Management Commands

### Test Configuration
```bash
nginx -t
```

### Reload Nginx (after config changes)
```bash
systemctl reload nginx
```

### Restart Nginx
```bash
systemctl restart nginx
```

### Check Status
```bash
systemctl status nginx
```

### View Logs
```bash
# Access log
tail -f /var/log/nginx/b2b-contact-miner-access.log

# Error log
tail -f /var/log/nginx/b2b-contact-miner-error.log
```

## Architecture

```
Internet
    ↓
http://85.198.86.237 (Port 80)
    ↓
Nginx Reverse Proxy
    ↓ (proxy_pass)
http://127.0.0.1:5000
    ↓
Flask Web Server
    ↓
Application Logic + Database
```

## Security Notes

1. **Flask binds to localhost only** (127.0.0.1)
   - Not directly accessible from outside
   - All external traffic goes through nginx

2. **Nginx provides security layer**
   - Security headers
   - Request filtering
   - Rate limiting ready (can be added)

3. **Hidden files blocked**
   - .env, .git, etc. are not accessible

## Troubleshooting

### Nginx won't start
```bash
# Check configuration
nginx -t

# Check error log
journalctl -u nginx -f
```

### 502 Bad Gateway
```bash
# Check if Flask is running
supervisorctl status b2b-web

# Check Flask logs
tail -f /opt/b2b-contact-miner/logs/web_err.log
```

### Can't access from browser
```bash
# Check firewall
ufw status

# Allow port 80 if needed
ufw allow 80/tcp
```

## Future Enhancements

### Add HTTPS (Let's Encrypt)
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

### Add Rate Limiting
Add to nginx config:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location / {
    limit_req zone=api burst=20;
    ...
}
```

### Add Authentication
```nginx
location / {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    ...
}
```

## Deployment Updates

After updating the project:
1. Pull changes: `git pull`
2. Nginx config usually doesn't need changes
3. If config changed: `nginx -t && systemctl reload nginx`
