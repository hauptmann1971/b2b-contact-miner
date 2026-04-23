# Deployment Scripts

Scripts for deploying and managing the B2B Contact Miner application.

## Windows Deployment

### Start All Services (PowerShell)
```powershell
.\deploy\start_all.ps1
```

This script will:
1. Check Python installation
2. Create/activate virtual environment
3. Install dependencies
4. Initialize database
5. Start monitoring service
6. Provide instructions for main pipeline

### Start All Services (Batch)
```batch
deploy\start_all.bat
```

### Auto Deploy to Server
```powershell
.\deploy\auto_deploy.ps1
```

Automatically deploys code to remote server via SSH.

## Linux Deployment

### Start All Services
```bash
chmod +x deploy/start_all.sh
./deploy/start_all.sh
```

### Manual Deploy Script
```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

For manual deployment to remote server with detailed instructions.

## What Each Script Does

### start_all.ps1 / start_all.sh / start_all.bat
Complete setup and startup script that:
- Validates environment
- Sets up virtual environment
- Installs dependencies from requirements.txt
- Initializes database
- Starts FastAPI monitoring service
- Provides next steps for running the main pipeline

### auto_deploy.ps1
Automated deployment to remote server:
- Syncs code via git
- Updates dependencies
- Restarts services
- Requires SSH key authentication

### deploy.sh
Manual deployment helper:
- Shows step-by-step instructions
- Provides commands for remote server management
- Includes troubleshooting tips

## Prerequisites

- Python 3.10+
- Git
- SSH access to server (for remote deployment)
- MySQL database configured in .env

## Configuration

All scripts use the `.env` file in project root for configuration.
Make sure to set up your environment variables before running:

```env
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db
REDIS_URL=redis://localhost:6379/0
# ... other settings
```

## Troubleshooting

If scripts fail:
1. Check that `.env` file exists and is configured
2. Verify Python version: `python --version`
3. Check database connectivity
4. Review logs in `logs/` directory
5. Run validation: `python scripts/validate_setup.py`
