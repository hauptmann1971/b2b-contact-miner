import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy import text
from models.database import SessionLocal, engine
from workers.db_task_queue import DatabaseTaskQueue
from config.settings import settings
from datetime import datetime, timezone
from loguru import logger
from functools import lru_cache

# Database health check query
DB_HEALTH_CHECK = "SELECT 1"

app = FastAPI(title="Contact Miner Health Check", version="1.0.0")

# Enable CORS for Flask web server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global reference to task queue (set by main.py when running pipeline)
task_queue: DatabaseTaskQueue = None


@app.on_event("startup")
async def startup_event():
    global redis_client, task_queue
    logger.info("Health check API started")


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, Any]
    queue_size: int
    uptime_seconds: float


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    start_time = datetime.now(timezone.utc)
    
    services_status = {}
    
    # Check database with latency measurement
    try:
        db_start = datetime.now(timezone.utc)
        db = SessionLocal()
        db.execute(text(DB_HEALTH_CHECK))
        db.close()
        db_latency = round((datetime.now(timezone.utc) - db_start).total_seconds() * 1000, 2)
        
        services_status["database"] = {
            "status": "healthy",
            "latency_ms": db_latency
        }
    except Exception as e:
        services_status["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check task queue (now uses database) - optimized to avoid extra DB calls when not needed
    try:
        if task_queue:
            # Only get stats if queue is initialized (fast operation)
            stats = await task_queue.get_queue_stats()
            services_status["task_queue"] = {
                "status": "healthy",
                "type": "database",
                "pending_tasks": stats.get('pending', 0),
                "running_tasks": stats.get('running', 0),
                "completed_tasks": stats.get('completed', 0),
                "failed_tasks": stats.get('failed', 0),
                "total_tasks": stats.get('total', 0),
                "active_workers": stats.get('current_workers', 0)
            }
        else:
            # Read stats directly from database when queue object not available
            db = SessionLocal()
            result = db.execute(text("SHOW TABLES LIKE 'task_queue'")).fetchone()
            
            if result:
                # Table exists - read stats from database
                pending = db.execute(text("SELECT COUNT(*) FROM task_queue WHERE status = 'pending'")).scalar()
                running = db.execute(text("SELECT COUNT(*) FROM task_queue WHERE status = 'running'")).scalar()
                completed = db.execute(text("SELECT COUNT(*) FROM task_queue WHERE status = 'completed'")).scalar()
                failed = db.execute(text("SELECT COUNT(*) FROM task_queue WHERE status = 'failed'")).scalar()
                total = db.execute(text("SELECT COUNT(*) FROM task_queue")).scalar()
                db.close()
                
                if total > 0 or pending > 0 or running > 0:
                    services_status["task_queue"] = {
                        "status": "healthy",
                        "type": "database",
                        "pending_tasks": pending,
                        "running_tasks": running,
                        "completed_tasks": completed,
                        "failed_tasks": failed,
                        "total_tasks": total,
                        "active_workers": 0,
                        "note": "Reading from database (queue workers not in this process)"
                    }
                else:
                    services_status["task_queue"] = {
                        "status": "available",
                        "type": "database",
                        "note": "Table exists but no tasks yet"
                    }
            else:
                db.close()
                services_status["task_queue"] = {
                    "status": "not_configured",
                    "note": "Run migration: migrations/add_task_queue_table.sql"
                }
    except Exception as e:
        services_status["task_queue"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    all_healthy = all(
        s.get("status") in ["healthy", "available"] 
        for s in services_status.values()
    )
    queue_quality_degraded = False
    queue_stats = services_status.get("task_queue", {})
    timeout_rate = float(queue_stats.get("timeout_rate_24h", 0.0) or 0.0)
    contacts_rate = float(queue_stats.get("domains_with_contacts_rate_24h", 0.0) or 0.0)
    if timeout_rate >= settings.TIMEOUT_RATE_ALERT_THRESHOLD_PCT:
        queue_quality_degraded = True
    if contacts_rate <= settings.CONTACTS_RATE_ALERT_THRESHOLD_PCT and queue_stats.get("total_tasks", 0):
        queue_quality_degraded = True
    
    total_time = round((datetime.now(timezone.utc) - start_time).total_seconds() * 1000, 2)
    
    return HealthResponse(
        status="degraded" if (all_healthy and queue_quality_degraded) else ("healthy" if all_healthy else "unhealthy"),
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services_status,
        queue_size=services_status.get("task_queue", {}).get("pending_tasks", 0),
        uptime_seconds=total_time
    )


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        db = SessionLocal()
        db.execute(text(DB_HEALTH_CHECK))
        db.close()
        
        return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/metrics/pipeline")
async def pipeline_metrics():
    """Get pipeline execution metrics with queue stats"""
    from utils.state_manager import StateManager
    
    state_manager = StateManager()
    stats = state_manager.get_last_run_status()
    
    # Get queue stats if available
    queue_stats = {}
    try:
        if task_queue:
            queue_stats = await task_queue.get_queue_stats()
        else:
            # Read queue quality metrics directly from DB when worker queue is not attached
            queue_stats = await DatabaseTaskQueue(max_concurrent=1).get_queue_stats()
    except Exception as e:
        logger.warning(f"Failed to get queue stats: {e}")
    
    return {
        "pipeline": stats,
        "queue": queue_stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def _measure_async_latency(func) -> float:
    """Measure async function execution latency in ms"""
    import time
    import asyncio
    start = time.time()
    try:
        asyncio.run(func())
    except Exception:
        pass
    return round((time.time() - start) * 1000, 2)


def _measure_db_latency() -> float:
    """Measure database query latency"""
    import time
    start = time.time()
    try:
        db = SessionLocal()
        db.execute(text(DB_HEALTH_CHECK))
        db.close()
    except Exception:
        pass
    return round((time.time() - start) * 1000, 2)


if __name__ == "__main__":
    import uvicorn
    # SECURITY: Bind to localhost only (not all interfaces)
    # Use host='0.0.0.0' only if external access is required with proper firewall rules
    uvicorn.run(app, host="127.0.0.1", port=8000)
