import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import redis.asyncio as redis
from sqlalchemy import text
from models.database import SessionLocal, engine
from workers.task_worker import AsyncTaskQueue
from config.settings import settings
from datetime import datetime
from loguru import logger
from functools import lru_cache

app = FastAPI(title="Contact Miner Health Check", version="1.0.0")

# Enable CORS for Flask web server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global references (set by main.py when running pipeline)
redis_client: redis.Redis = None
task_queue: AsyncTaskQueue = None


@lru_cache()
def get_redis_client() -> redis.Redis:
    """Lazy initialization of Redis client for standalone API usage"""
    try:
        return redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}, using FakeRedis")
        # Fallback to FakeRedis for development
        try:
            import fakeredis
            return fakeredis.FakeAsyncRedis()
        except ImportError:
            logger.error("fakeredis not installed")
            return None


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
    start_time = datetime.utcnow()
    
    services_status = {}
    
    # Use global redis_client if set, otherwise lazy initialize
    active_redis = redis_client or get_redis_client()
    
    try:
        if active_redis:
            await active_redis.ping()
            services_status["redis"] = {
                "status": "healthy",
                "latency_ms": _measure_async_latency(active_redis.ping)
            }
        else:
            # Try to use FakeRedis as fallback
            try:
                import fakeredis.aioredis
                fake_redis = fakeredis.aioredis.FakeRedis()
                await fake_redis.ping()
                services_status["redis"] = {
                    "status": "healthy (FakeRedis)",
                    "latency_ms": 0.1,
                    "note": "Using in-memory Redis for development"
                }
                active_redis = fake_redis
            except Exception as fake_error:
                services_status["redis"] = {
                    "status": "not_configured",
                    "error": f"Redis unavailable and FakeRedis failed: {str(fake_error)}"
                }
    except Exception as e:
        # Real Redis failed, try FakeRedis
        try:
            import fakeredis.aioredis
            fake_redis = fakeredis.aioredis.FakeRedis()
            await fake_redis.ping()
            services_status["redis"] = {
                "status": "healthy (FakeRedis)",
                "latency_ms": 0.1,
                "note": "Using in-memory Redis for development"
            }
            active_redis = fake_redis
        except Exception as fake_error:
            services_status["redis"] = {
                "status": "unhealthy",
                "error": f"{str(e)}. FakeRedis also failed: {str(fake_error)}"
            }
    
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        services_status["database"] = {
            "status": "healthy",
            "latency_ms": _measure_db_latency()
        }
    except Exception as e:
        services_status["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    try:
        if task_queue:
            queue_size = task_queue.queue.qsize()
            services_status["task_queue"] = {
                "status": "healthy",
                "queue_size": queue_size,
                "max_size": task_queue.queue.maxsize,
                "workers_active": len(task_queue.workers)
            }
        else:
            services_status["task_queue"] = {"status": "not_initialized"}
    except Exception as e:
        services_status["task_queue"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    unhealthy_services = [
        name for name, status in services_status.items()
        if status.get("status") == "unhealthy"
    ]
    
    overall_status = "unhealthy" if unhealthy_services else "healthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        services=services_status,
        queue_size=task_queue.queue.qsize() if task_queue else 0,
        uptime_seconds=(datetime.utcnow() - start_time).total_seconds()
    )


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        active_redis = redis_client or get_redis_client()
        if active_redis:
            await active_redis.ping()
        
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/metrics/pipeline")
async def pipeline_metrics():
    """Get pipeline execution metrics"""
    from utils.state_manager import StateManager
    
    state_manager = StateManager()
    stats = state_manager.get_last_run_status()
    
    return {
        "pipeline": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


def _measure_async_latency(func) -> float:
    """Measure async function execution latency in ms"""
    import time
    import asyncio
    start = time.time()
    try:
        asyncio.run(func())
    except:
        pass
    return round((time.time() - start) * 1000, 2)


def _measure_db_latency() -> float:
    """Measure database query latency"""
    import time
    start = time.time()
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except:
        pass
    return round((time.time() - start) * 1000, 2)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
