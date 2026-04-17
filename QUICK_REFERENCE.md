# Quick Reference - B2B Contact Miner

## 🚀 Quick Start

### First Time Setup
```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Validate setup
python validate_setup.py

# 4. Start all services
./start_all.sh start        # Linux/Mac
start_all.bat start         # Windows CMD
.\start_all.ps1 start       # Windows PowerShell
```

### Daily Usage
```bash
# Start services
./start_all.sh start

# Check status
./start_all.sh status

# View logs
./start_all.sh logs

# Stop services
./start_all.sh stop
```

## 📋 Common Commands

### Service Management
```bash
# Start/Stop/Restart
./start_all.sh start
./start_all.sh stop
./start_all.sh restart

# Check what's running
./start_all.sh status

# Clean up old files
./start_all.sh clean
```

### Logs
```bash
# All logs
./start_all.sh logs

# Specific service
./start_all.sh logs monitoring
./start_all.sh logs web_server
./start_all.sh logs scheduler
```

### Pipeline Execution
```bash
# Run manually (on-demand)
python main.py

# Or wait for scheduler (runs daily at 02:00)
```

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Web UI | http://localhost:5000 | Main dashboard |
| Keywords | http://localhost:5000/keywords | Manage keywords |
| Contacts | http://localhost:5000/contacts | View contacts |
| Health | http://localhost:8000/health | System health |
| API Docs | http://localhost:8000/docs | FastAPI docs |
| Stats API | http://localhost:5000/api/stats | Statistics |

## 🔧 Troubleshooting

### Services Won't Start
```bash
# 1. Validate environment
python validate_setup.py

# 2. Check logs
./start_all.sh logs

# 3. Clean and restart
./start_all.sh stop
./start_all.sh clean
./start_all.sh start
```

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000          # Linux/Mac
netstat -ano | findstr :5000   # Windows

# Kill the process
kill <PID>             # Linux/Mac
taskkill /PID <PID> /F # Windows
```

### Database Issues
```sql
-- Connect to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE contact_miner;

-- Grant permissions
GRANT ALL PRIVILEGES ON contact_miner.* TO 'user'@'localhost';
FLUSH PRIVILEGES;
```

### Redis Not Starting
```bash
# With Docker
cd doc
docker-compose up -d redis

# Or install locally
# Ubuntu: sudo apt install redis-server
# Mac: brew install redis
# Windows: Use Docker or WSL
```

## 📊 Monitoring

### Check Service Health
```bash
# Command line
./start_all.sh status

# Web interface
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:5000/api/stats
```

### View Recent Activity
```bash
# Last 50 lines of all logs
tail -n 50 logs/*.log

# Follow logs in real-time
./start_all.sh logs

# Search for errors
grep -i error logs/*.log
```

## 🎯 Typical Workflow

### 1. Add Keywords
```bash
# Via web UI
Open http://localhost:5000
Click "Add Keyword"
Enter keyword, language, country

# Or via API
curl -X POST http://localhost:5000/add_keyword \
  -d "keyword=B2B software&language=en&country=US"
```

### 2. Run Pipeline
```bash
# Manual run
python main.py

# Or wait for automatic run (daily at 02:00)
```

### 3. View Results
```bash
# Web UI
Open http://localhost:5000/contacts

# API
curl http://localhost:5000/api/stats
```

### 4. Export Data
```bash
# Via web UI
Go to Contacts page
Click "Export to CSV" or "Export to Excel"
```

## 🔑 Environment Variables

Essential variables in `.env`:

```env
# Database (required)
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/contact_miner

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# SERP API (required for search)
SERP_API_PROVIDER=serpapi
SERPAPI_KEY=your_api_key_here

# Crawler settings
MAX_PAGES_PER_DOMAIN=10
CONCURRENT_BROWSERS=5
HEADLESS_BROWSER=true

# LLM (optional)
OPENAI_API_KEY=your_openai_key
USE_LLM_EXTRACTION=false
```

## 📁 Important Files

```
b2b-contact-miner/
├── main.py                  # Main pipeline (run manually)
├── web_server.py            # Flask web server
├── scheduler.py             # Daily scheduler
├── monitoring/
│   └── healthcheck.py       # FastAPI health checks
├── start_all.sh/bat/ps1     # Startup scripts
├── validate_setup.py        # Environment validator
├── .env                     # Your configuration
├── logs/                    # Service logs
└── pids/                    # Process IDs
```

## 🐛 Debug Mode

### Enable Verbose Logging
Edit `.env`:
```env
LOG_LEVEL=DEBUG
```

### Run Single Service
```bash
# Instead of start_all, run individually
python web_server.py           # Flask
uvicorn monitoring.healthcheck:app --reload  # FastAPI
python scheduler.py            # Scheduler
python main.py                 # Pipeline
```

### Database Direct Access
```python
# Quick DB query
python -c "
from models.database import SessionLocal, Keyword
db = SessionLocal()
keywords = db.query(Keyword).all()
for k in keywords:
    print(f'{k.id}: {k.keyword}')
db.close()
"
```

## 💡 Tips & Tricks

### Speed Up Development
```bash
# Use hot reload for web server
# Edit web_server.py, add:
app.run(debug=True, use_reloader=True)

# For FastAPI, use --reload flag
uvicorn monitoring.healthcheck:app --reload
```

### Backup Database
```bash
mysqldump -u user -p contact_miner > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
mysql -u user -p contact_miner < backup_20240101.sql
```

### Clear Old Data
```sql
-- Delete old crawl logs
DELETE FROM crawl_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Reset keywords for re-crawling
UPDATE keywords SET is_processed = FALSE;
```

## 📞 Getting Help

1. **Check logs**: `./start_all.sh logs`
2. **Validate setup**: `python validate_setup.py`
3. **Read docs**: See `doc/` folder
4. **Check status**: `./start_all.sh status`
5. **Review this guide**: `cat QUICK_REFERENCE.md`

## 🎓 Learning Resources

- **Architecture**: See `doc/ARCHITECTURE.md`
- **API Keys Setup**: See `doc/API_KEYS_SETUP.md`
- **How It Works**: See `doc/HOW_IT_WORKS.md`
- **Startup Guide**: See `STARTUP_SCRIPTS_GUIDE.md`

---

**Remember**: Always run `python validate_setup.py` before troubleshooting!
