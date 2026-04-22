# SonarQube Integration Guide

## 📋 Overview

SonarQube has been successfully deployed on the production server for continuous code quality analysis.

**Server**: http://85.198.86.237:9000  
**Default Credentials**: admin / admin  
**Version**: 26.4.0 (Community Edition)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Production Server                   │
│         (85.198.86.237)                     │
├─────────────────────────────────────────────┤
│                                             │
│  Docker Containers:                         │
│  ┌──────────────┐    ┌──────────────────┐  │
│  │  SonarQube   │    │   PostgreSQL     │  │
│  │  Port: 9000  │◄──►│   Database       │  │
│  └──────────────┘    └──────────────────┘  │
│                                             │
│  Application:                               │
│  ┌──────────────────────────────────┐      │
│  │  B2B Contact Miner               │      │
│  │  - web_server.py (supervisord)   │      │
│  │  - main.py (pipeline)            │      │
│  └──────────────────────────────────┘      │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🚀 Deployment Details

### What Was Done:

#### 1. **Docker Installation** ✅
- Installed Docker CE 29.4.1
- Installed Docker Compose Plugin v5.1.3
- Configured system requirements (vm.max_map_count)

#### 2. **SonarQube Setup** ✅
- Created `/opt/sonarqube/` directory
- Deployed docker-compose.yml with:
  - SonarQube Community Edition container
  - PostgreSQL 15 database container
  - Persistent volumes for data
  - Network isolation

#### 3. **System Configuration** ✅
- Set `vm.max_map_count=524288` (required by Elasticsearch)
- Set `fs.file-max=131072` (file descriptor limit)
- Made settings persistent in `/etc/sysctl.conf`

#### 4. **Project Configuration** ✅
- Created `sonar-project.properties` in project root
- Configured Python-specific analysis rules
- Set up test coverage integration

---

## 📊 Accessing SonarQube

### Web Interface
```
URL: http://85.198.86.237:9000
Username: admin
Password: admin  # Change this immediately!
```

### First Login Steps:
1. Navigate to http://85.198.86.237:9000
2. Login with admin/admin
3. **IMPORTANT**: Change default password immediately
4. Go to My Account → Security → Update Token
5. Generate a new token for CLI access

---

## 🔧 Running Analysis

### Option 1: Local Analysis (Development)

Install SonarScanner:
```bash
# Windows
choco install sonarqube-scanner

# Linux
sudo apt-get install sonar-scanner

# Or download from https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/
```

Run analysis:
```bash
cd c:\Users\romanov\PycharmProjects\b2b-contact-miner
sonar-scanner -Dsonar.host.url=http://85.198.86.237:9000 -Dsonar.login=YOUR_TOKEN
```

---

### Option 2: Remote Analysis (On Server)

SSH to server:
```bash
ssh root@85.198.86.237
cd /opt/b2b-contact-miner

# Install sonar-scanner
pip install sonar-scanner

# Run analysis
sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.login=YOUR_TOKEN
```

---

### Option 3: Automated via CI/CD

Create `.github/workflows/sonarqube.yml`:
```yaml
name: SonarQube Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests with coverage
      run: |
        pytest --cov=. --cov-report=xml --junitxml=test-results.xml tests/
    
    - name: SonarQube Scan
      uses: SonarSource/sonarqube-scan-action@v3
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        SONAR_HOST_URL: http://85.198.86.237:9000
```

---

## 📈 What SonarQube Analyzes

### Code Quality Metrics:
- **Bugs**: Potential errors that will break functionality
- **Vulnerabilities**: Security weaknesses
- **Code Smells**: Maintainability issues
- **Coverage**: Test coverage percentage
- **Duplications**: Duplicated code blocks
- **Complexity**: Cyclomatic and cognitive complexity

### Python-Specific Rules:
- PEP 8 compliance
- Type hints usage
- Unused imports/variables
- Hardcoded credentials
- SQL injection risks
- Exception handling
- Function length and complexity

---

## 🎯 Quality Gates

Default Quality Gate thresholds:
```
✅ New Code Coverage ≥ 80%
✅ New Duplicated Lines ≤ 3%
✅ New Bugs = 0
✅ New Vulnerabilities = 0
✅ New Security Hotspots Reviewed = 100%
✅ Maintainability Rating = A
✅ Reliability Rating = A
✅ Security Rating = A
```

If any threshold fails → Quality Gate fails → PR cannot be merged

---

## 🔐 Security Best Practices

### 1. Change Default Password
```bash
# After first login, go to:
My Account → Security → Update Password
```

### 2. Use Tokens Instead of Passwords
```bash
# Generate token in:
Administration → Security → Users → Tokens

# Use token for CLI:
sonar-scanner -Dsonar.login=YOUR_TOKEN
```

### 3. Restrict Network Access
```bash
# Add firewall rule (if needed)
ufw allow from YOUR_IP to any port 9000
```

### 4. Enable HTTPS (Recommended)
Use Nginx reverse proxy with Let's Encrypt SSL certificate.

---

## 🛠️ Management Commands

### Check Status
```bash
ssh root@85.198.86.237
docker ps | grep sonar
```

### View Logs
```bash
# SonarQube logs
docker logs sonarqube

# Database logs
docker logs sonarqube-db

# Follow logs in real-time
docker logs -f sonarqube
```

### Restart Services
```bash
cd /opt/sonarqube
docker compose restart
```

### Stop Services
```bash
cd /opt/sonarqube
docker compose down
```

### Update SonarQube
```bash
cd /opt/sonarqube
docker compose pull
docker compose up -d
```

### Backup Data
```bash
# Backup PostgreSQL database
docker exec sonarqube-db pg_dump -U sonar sonar > sonar_backup.sql

# Backup volumes
docker run --rm -v sonarqube_sonarqube_data:/data -v $(pwd):/backup alpine tar czf /backup/sonarqube_data.tar.gz -C /data .
```

---

## 📊 Integration with B2B Contact Miner

### Automatic Analysis on Pipeline Completion

Add to `main.py` after pipeline completion:
```python
import subprocess

def run_sonarqube_analysis():
    """Run SonarQube analysis after pipeline completes"""
    try:
        result = subprocess.run(
            ['sonar-scanner', 
             '-Dsonar.host.url=http://localhost:9000',
             '-Dsonar.login=TOKEN'],
            cwd='/opt/b2b-contact-miner',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("SonarQube analysis completed successfully")
        else:
            logger.error(f"SonarQube analysis failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Failed to run SonarQube: {e}")
```

---

## 🐛 Troubleshooting

### Issue: SonarQube Not Starting

**Symptoms**: Container exits immediately

**Solution**:
```bash
# Check logs
docker logs sonarqube

# Common fix: Increase vm.max_map_count
sysctl -w vm.max_map_count=524288

# Restart
docker compose restart
```

---

### Issue: Out of Memory

**Symptoms**: Container killed by OOM killer

**Solution**:
```bash
# Check memory usage
docker stats sonarqube

# Increase Docker memory limit or add swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

### Issue: Cannot Connect to Database

**Symptoms**: "Connection refused" errors

**Solution**:
```bash
# Check if DB is running
docker ps | grep postgres

# Check DB logs
docker logs sonarqube-db

# Restart DB
docker compose restart db
```

---

### Issue: Slow Performance

**Solutions**:
1. Increase JVM heap size in docker-compose.yml:
```yaml
environment:
  SONAR_WEB_JAVAADDITIONALOPTS: "-Xmx2g -Xms512m"
```

2. Add more RAM to server (minimum 4GB recommended)

3. Use SSD storage for volumes

---

## 📚 Additional Resources

- **Official Documentation**: https://docs.sonarqube.org/
- **Python Rules**: https://rules.sonarsource.com/python/
- **Quality Gates**: https://docs.sonarqube.org/latest/user-guide/quality-gates/
- **CI/CD Integration**: https://docs.sonarqube.org/latest/devops-platform-integration/github-integration/

---

## ✅ Next Steps

1. **Change default password** immediately
2. **Generate API token** for automated scans
3. **Configure Quality Gates** according to project needs
4. **Add SonarQube badge** to README.md
5. **Set up notifications** (Slack/Email) for quality gate failures
6. **Schedule regular scans** (daily/weekly)
7. **Review and fix** existing code issues
8. **Add test coverage** to reach 80% target

---

## 🎉 Success Criteria

SonarQube integration is successful when:
- ✅ SonarQube is accessible at http://85.198.86.237:9000
- ✅ First analysis completes without errors
- ✅ Quality Gate passes for new code
- ✅ Team is trained on fixing issues
- ✅ Automated scans are configured in CI/CD
- ✅ Code quality trends are improving

---

**Last Updated**: 2026-04-22  
**Status**: ✅ Deployed and Running
