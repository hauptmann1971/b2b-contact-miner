# Startup Scripts Guide

This document explains how to use the startup scripts for B2B Contact Miner.

## Overview

The project includes three startup scripts for different operating systems:
- **start_all.bat** - Windows Batch script
- **start_all.ps1** - Windows PowerShell script  
- **start_all.sh** - Linux/Mac Bash script

All scripts provide the same functionality with platform-specific implementations.

## Prerequisites

Before running the startup scripts, ensure you have:

1. **Python 3.8+** installed and in PATH
2. **.env file** configured (copy from `.env.example`)
3. **Dependencies installed**: `pip install -r requirements.txt`
4. **Database server** running (MySQL/MariaDB)
5. **Redis** (optional, but recommended)

## Quick Start

### Windows (Batch)
```batch
start_all.bat start
```

### Windows (PowerShell)
```powershell
.\start_all.ps1 start
```

### Linux/Mac
```bash
chmod +x start_all.sh
./start_all.sh start
```

## Available Commands

All scripts support the following commands:

| Command | Description |
|---------|-------------|
| `start` | Start all services (default) |
| `stop` | Stop all services |
| `restart` | Restart all services |
| `status` | Show service status |
| `logs [service]` | View logs (all or specific service) |
| `clean` | Remove PID files and old logs |

### Examples

```bash
# Start all services
./start_all.sh start

# Check status
./start_all.sh status

# View all logs
./start_all.sh logs

# View specific service logs
./start_all.sh logs web_server

# Stop everything
./start_all.sh stop

# Clean up
./start_all.sh clean
```

## Services Started

The startup scripts manage the following services:

### 1. FastAPI Monitoring Server (Port 8000)
- **Purpose**: Health checks and monitoring API
- **Endpoints**:
  - `http://localhost:8000/health` - Full health check
  - `http://localhost:8000/health/live` - Liveness probe
  - `http://localhost:8000/health/ready` - Readiness probe
  - `http://localhost:8000/docs` - API documentation
- **Started with**: `uvicorn monitoring.healthcheck:app`

### 2. Flask Web Server (Port 5000)
- **Purpose**: Main web UI and REST API
- **Endpoints**:
  - `http://localhost:5000` - Web dashboard
  - `http://localhost:5000/keywords` - Keywords management
  - `http://localhost:5000/contacts` - Contacts list
  - `http://localhost:5000/api/stats` - Statistics API
  - `http://localhost:5000/health` - Health check
- **Started with**: `python web_server.py`

### 3. Task Scheduler
- **Purpose**: Automated daily pipeline execution
- **Schedule**: Runs daily at 02:00 AM
- **Started with**: `python scheduler.py`
- **Note**: Can be manually triggered via `python main.py`

## Startup Process

The scripts follow this sequence:

1. **[0/7] Prerequisites Check**
   - Verify `.env` file exists
   - Check Python installation
   - Activate virtual environment (if exists)

2. **[1/7] Database Initialization**
   - Create tables if they don't exist
   - Verify database connectivity

3. **[2/7] FastAPI Monitoring Server**
   - Start uvicorn on port 8000
   - Wait for service to be ready

4. **[3/7] Flask Web Server**
   - Start Flask on port 5000
   - Initialize templates and routes

5. **[4/7] Task Scheduler**
   - Start background scheduler
   - Set up daily cron job

6. **[5/7] Pipeline Status**
   - Display manual run instructions

7. **[6/7] Service Status Check**
   - Verify all services are running
   - Display PIDs and ports

8. **[7/7] Docker Status**
   - Check Docker Compose services (if available)
   - Display container status

## Log Files

All services log to the `logs/` directory:

```
logs/
├── monitoring.log      # FastAPI server logs
├── monitoring.log.out  # stdout output
├── monitoring.log.err  # stderr output
├── web_server.log      # Flask server logs
├── web_server.log.out  # stdout output
├── web_server.log.err  # stderr output
├── scheduler.log       # Scheduler logs
├── scheduler.log.out   # stdout output
└── scheduler.log.err   # stderr output
```

## PID Files

Process IDs are stored in the `pids/` directory for service management:

```
pids/
├── monitoring.pid
├── web_server.pid
└── scheduler.pid
```

## Manual Pipeline Execution

To run the contact mining pipeline manually:

```bash
python main.py
```

This will:
1. Fetch pending keywords from database
2. Search for websites using SERP API
3. Crawl websites and extract contacts
4. Save results to database

## Troubleshooting

### Service Won't Start

1. **Check logs**:
   ```bash
   ./start_all.sh logs <service_name>
   ```

2. **Verify prerequisites**:
   - Python is installed: `python --version`
   - Dependencies installed: `pip list`
   - .env file configured

3. **Check port availability**:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :5000
   lsof -i :8000
   ```

### Database Connection Failed

1. Verify MySQL is running
2. Check DATABASE_URL in `.env`
3. Ensure database exists:
   ```sql
   CREATE DATABASE contact_miner;
   ```

### Redis Not Available

Redis is optional. The system will fall back to in-memory deduplication if Redis is not running.

To start Redis with Docker:
```bash
cd doc
docker-compose up -d redis
```

### Clean Restart

If services are in a bad state:

```bash
# Stop all services
./start_all.sh stop

# Clean PID files
./start_all.sh clean

# Start fresh
./start_all.sh start
```

## Virtual Environment

If you're using a virtual environment:

```bash
# Create venv (first time only)
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# The startup scripts will auto-detect and activate venv
./start_all.sh start
```

## Docker Integration

The scripts can optionally manage Docker services (Redis, MySQL):

1. Edit `doc/docker-compose.yml` as needed
2. Start Docker services:
   ```bash
   cd doc
   docker-compose up -d
   ```
3. The startup scripts will detect and display Docker status

## Architecture

```
┌─────────────────────────────────────┐
│     User / Browser                  │
└──────────┬──────────────────────────┘
           │
    ┌──────▼────────┐
    │  Flask Web     │  Port 5000
    │  Server        │  - Web UI
    │                │  - REST API
    └──────┬─────────┘
           │
    ┌──────▼────────┐
    │  FastAPI       │  Port 8000
    │  Monitoring    │  - Health checks
    │                │  - Metrics
    └──────┬─────────┘
           │
    ┌──────▼────────┐
    │  Scheduler     │  Background
    │                │  - Daily runs
    └──────┬─────────┘
           │
    ┌──────▼────────┐
    │  Main Pipeline │  On-demand
    │  (main.py)     │  - SERP search
    │                │  - Web crawling
    │                │  - Contact extraction
    └──────┬─────────┘
           │
    ┌──────▼────────┐
    │  Database      │  MySQL
    │  & Redis       │  Data storage
    └───────────────┘
```

## Best Practices

1. **Always check status** after starting:
   ```bash
   ./start_all.sh status
   ```

2. **Monitor logs** during first run:
   ```bash
   ./start_all.sh logs
   ```

3. **Use restart** instead of stop/start:
   ```bash
   ./start_all.sh restart
   ```

4. **Clean periodically** to remove old logs:
   ```bash
   ./start_all.sh clean
   ```

5. **Run pipeline manually** to test:
   ```bash
   python main.py
   ```

## Environment Variables

Key variables in `.env`:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/contact_miner
REDIS_URL=redis://localhost:6379/0
SERP_API_PROVIDER=serpapi
SERPAPI_KEY=your_key_here
MAX_CONCURRENT_DOMAINS=5
USE_LLM_EXTRACTION=false
```

See `.env.example` for all available options.

## Support

For issues:
1. Check logs: `./start_all.sh logs`
2. Verify status: `./start_all.sh status`
3. Review documentation in `doc/` folder
4. Check GitHub issues
