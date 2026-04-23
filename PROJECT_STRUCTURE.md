# B2B Contact Miner - Project Structure

## 📁 Directory Layout

```
b2b-contact-miner/
│
├── 📄 Core Files (Root)
│   ├── main.py                 # Main pipeline entry point
│   ├── web_server.py           # Flask web UI server
│   ├── api_server.py           # FastAPI REST API server
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (not in git)
│   ├── .env.example            # Template for .env
│   └── sonar-project.properties # SonarCloud configuration
│
├── 📂 src/                     # Source code modules
│   ├── checkers/               # Keyword and data validation
│   ├── config/                 # Configuration management
│   ├── getters/                # Data retrieval utilities
│   ├── models/                 # Database models & schemas
│   ├── services/               # Business logic services
│   ├── utils/                  # Utility functions
│   ├── workers/                # Background task workers
│   └── monitoring/             # Health check & monitoring
│
├── 📂 scripts/                 # Utility scripts
│   ├── export_*.py            # Data export scripts
│   ├── check_*.py             # Database check scripts
│   ├── test_*.py              # Test scripts
│   ├── monitor_workers.py     # Worker monitoring
│   ├── validate_setup.py      # Setup validation
│   └── download_sonar_report.py # SonarCloud report downloader
│
├── 📂 deploy/                  # Deployment scripts
│   ├── start_all.ps1          # Windows PowerShell startup
│   ├── start_all.bat          # Windows Batch startup
│   ├── start_all.sh           # Linux/Mac startup
│   ├── auto_deploy.ps1        # Automated deployment
│   └── deploy.sh              # Manual deployment helper
│
├── 📂 tests/                   # Unit & integration tests
├── 📂 migrations/              # Database migrations (Alembic)
├── 📂 templates/               # HTML templates for Flask UI
├── 📂 doc/                     # Documentation
├── 📂 logs/                    # Application logs (not in git)
│
└── 📂 .github/                 # GitHub Actions workflows
    └── workflows/
        └── sonarcloud.yml     # SonarCloud CI/CD analysis
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use any text editor
```

### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python -c "from models.database import init_db; init_db()"
```

### 4. Run Application

**Option A: Use startup script (Recommended)**
```bash
# Windows
.\deploy\start_all.ps1

# Linux/Mac
chmod +x deploy/start_all.sh
./deploy/start_all.sh
```

**Option B: Manual start**
```bash
# Start monitoring service
python monitoring/healthcheck.py

# Start web UI
python web_server.py

# Run main pipeline
python main.py
```

## 📊 Monitoring & UI

- **Web UI**: http://localhost:5000
- **Health Check API**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

## 🔧 Common Tasks

### Run Specific Script
```bash
cd scripts
python validate_setup.py       # Validate setup
python check_contacts.py       # Check database contacts
python export_flat.py          # Export to CSV
python monitor_workers.py      # Monitor workers
```

### Deploy to Server
```bash
# Windows
.\deploy\auto_deploy.ps1

# Linux
./deploy/deploy.sh
```

### Run Tests
```bash
pytest tests/
```

### Code Quality Check
```bash
# SonarCloud analysis runs automatically on push
# View results at: https://sonarcloud.io/dashboard?id=hauptmann1971_b2b-contact-miner

# Download report locally
python scripts/download_sonar_report.py
```

## 📝 Key Files Explained

| File | Purpose |
|------|---------|
| `main.py` | Main pipeline orchestrator - crawls, extracts, stores contacts |
| `web_server.py` | Flask web interface for viewing results |
| `api_server.py` | FastAPI REST API for programmatic access |
| `scheduler.py` | Task scheduler for automated runs |
| `.env` | Configuration (DB credentials, API keys) - **NEVER commit!** |

## 🔐 Security Notes

- `.env` file contains secrets - never commit to Git
- Use environment variables for sensitive data
- SonarCloud scans for vulnerabilities on every push
- Network services bind to localhost by default

## 📖 Documentation

See `doc/` directory for detailed documentation:
- `SONARCLOUD_SETUP.md` - SonarCloud integration guide
- Other project-specific docs

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests: `pytest tests/`
4. Push to GitHub (SonarCloud will analyze)
5. Create pull request

## 📞 Support

For issues or questions, check:
1. Logs in `logs/` directory
2. Documentation in `doc/`
3. SonarCloud dashboard for code quality issues
