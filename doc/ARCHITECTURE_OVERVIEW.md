# Architecture Overview - Quick Reference

## 📚 Documentation Index

### C4 Architecture Diagrams
- **[C4_ARCHITECTURE.md](C4_ARCHITECTURE.md)** - Complete C4 diagrams (Context, Container, Component levels) with Mermaid syntax
- **[C4_DIAGRAM.html](C4_DIAGRAM.html)** - Interactive HTML visualization (open in browser)

### Database Documentation
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Complete database schema with field descriptions and relationships

### Project Structure
- **[PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)** - Directory layout and file organization

---

## 🎯 Quick Start - Understanding the Architecture

### 1. System at a Glance

```
User → Web UI (Flask) → MySQL Database
                      ↓
              Main Pipeline (main.py)
                      ↓
         SERP API → Crawl → LLM → Extract Contacts
```

### 2. Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **Main Pipeline** | `main.py` | Orchestrates search → crawl → extract workflow |
| **Web UI** | `web_server.py` | Flask dashboard for viewing results |
| **Monitoring API** | `api_server.py` | FastAPI health checks |
| **Task Queue** | `workers/db_task_queue.py` | Async task processing |
| **Database Models** | `models/database.py` | SQLAlchemy ORM models |

### 3. Data Flow

```
1. User adds keyword via Web UI
   ↓
2. Keyword stored in MySQL (keywords table)
   ↓
3. Main pipeline loads unprocessed keywords
   ↓
4. Search SERP API for keyword
   ↓
5. Crawl resulting websites with Playwright
   ↓
6. Extract contacts using LLM (YandexGPT/DeepSeek/OpenAI)
   ↓
7. Save contacts to MySQL (contacts table)
   ↓
8. Display results in Web UI
```

### 4. Technology Stack

**Backend:**
- Python 3.10+
- Flask 3.x (Web UI)
- FastAPI (Monitoring)
- SQLAlchemy (ORM)
- Playwright (Browser automation)

**Infrastructure:**
- MySQL 8.x (Database)
- Nginx (Reverse proxy)
- Supervisor (Process manager)

**AI/ML:**
- YandexGPT
- DeepSeek
- OpenAI

**DevOps:**
- GitHub Actions (CI/CD)
- SonarCloud (Code quality)

---

## 🔍 Where to Find What

### Looking for...

**How the pipeline works?**
→ See `main.py` and `doc/C4_ARCHITECTURE.md` (Component Diagram)

**Database structure?**
→ See `models/database.py` and `doc/DATABASE_SCHEMA.md`

**How tasks are queued?**
→ See `workers/db_task_queue.py` and `doc/C4_ARCHITECTURE.md` (Task Queue section)

**Web UI implementation?**
→ See `web_server.py` and `templates/` directory

**API endpoints?**
→ See `api_server.py` and visit http://localhost:8000/docs

**Configuration?**
→ See `config/settings.py` and `.env.example`

**Deployment setup?**
→ See `deploy/` directory and `doc/C4_ARCHITECTURE.md` (Deployment section)

---

## 📊 System Metrics

**Typical Scale:**
- Keywords: 100-500 per run
- Websites crawled: 1,000-5,000
- Contacts extracted: 5,000-20,000
- Processing time: 2-8 hours per run

**Performance:**
- SERP queries: ~1-2 seconds each
- Website crawl: ~5-30 seconds each
- LLM extraction: ~2-5 seconds each
- Database writes: ~10-50ms each

---

## 🛠️ Common Tasks

### Add a new keyword
1. Open Web UI: http://85.198.86.237
2. Go to "Keywords" tab
3. Click "Add Keyword"
4. Enter search query
5. Run pipeline: `python main.py`

### View extracted contacts
1. Open Web UI
2. Go to "Contacts" tab
3. Filter by domain/type
4. Export to CSV if needed

### Monitor pipeline progress
1. Check Web UI dashboard
2. Or run: `python scripts/monitor_workers.py`
3. Or check: `SELECT * FROM pipeline_state ORDER BY created_at DESC;`

### Check system health
```bash
curl http://85.198.86.237/health
# or
curl http://localhost:8000/health
```

---

## 🐛 Troubleshooting

**Pipeline not starting?**
- Check `.env` configuration
- Verify database connection
- Run: `python scripts/validate_setup.py`

**No contacts found?**
- Check SERP API credentials
- Verify LLM API keys
- Check `crawl_logs` table for errors

**Web UI not accessible?**
- Check Nginx status: `systemctl status nginx`
- Check Flask logs: `tail -f /opt/b2b-contact-miner/logs/web_err.log`
- Verify supervisor: `supervisorctl status`

**Task queue stuck?**
- Check: `SELECT * FROM task_queue WHERE status = 'running' AND locked_at < NOW() - INTERVAL 5 MINUTE;`
- Run: `python scripts/recover_stale_tasks.py`

---

## 📖 Additional Resources

- **SonarCloud Dashboard**: https://sonarcloud.io/dashboard?id=hauptmann1971_b2b-contact-miner
- **GitHub Repository**: https://github.com/hauptmann1971/b2b-contact-miner
- **Production Server**: http://85.198.86.237

---

*Last updated: 2026-04-23*
