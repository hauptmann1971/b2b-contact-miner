"""Database-backed task queue service"""
import json
import asyncio
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from loguru import logger
from models.database import SessionLocal
from models.task_queue import TaskQueue


class DatabaseTaskQueue:
    """Persistent task queue using MySQL database instead of Redis"""
    
    def __init__(self, max_concurrent: int = 20, lock_timeout: int = 300):
        self.max_concurrent = max_concurrent
        self.lock_timeout = lock_timeout  # seconds before lock expires
        self.running = False
        self.workers = []
        self.current_tasks = 0
        self.tasks_semaphore = asyncio.Semaphore(max_concurrent)
    
    async def start_workers(self):
        """Start worker tasks"""
        self.running = True
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        logger.info(f"Started {self.max_concurrent} database-backed workers")
    
    async def stop_workers(self):
        """Stop all workers gracefully"""
        self.running = False
        
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("All database workers stopped")
    
    async def add_task(self, task_name: str, task_type: str, payload: Dict, 
                      priority: int = 0, max_retries: int = 3, 
                      scheduled_for: Optional[datetime] = None):
        """Add task to database queue"""
        try:
            db = SessionLocal()
            task = TaskQueue(
                task_name=task_name,
                task_type=task_type,
                payload=json.dumps(payload),
                priority=priority,
                max_retries=max_retries,
                scheduled_for=scheduled_for,
                status='pending'
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.debug(f"Task added to DB queue: {task.id} ({task_type})")
            return task.id
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add task to DB: {e}")
            raise
        finally:
            db.close()
    
    async def _worker(self, worker_id: int):
        """Worker that processes tasks from database"""
        worker_name = f"db-worker-{worker_id}"
        
        while self.running:
            try:
                # Try to acquire semaphore (limits concurrent tasks)
                await asyncio.wait_for(self.tasks_semaphore.acquire(), timeout=2.0)
                
                # Fetch next pending task
                task = await self._fetch_next_task(worker_name)
                
                if task:
                    self.current_tasks += 1
                    try:
                        # Execute the task
                        await self._execute_task(task, worker_name)
                    except Exception as e:
                        logger.error(f"Worker {worker_id} task {task.id} failed: {e}")
                        await self._handle_task_failure(task.id, str(e))
                    finally:
                        self.current_tasks -= 1
                        self.tasks_semaphore.release()
                else:
                    # No tasks available, release semaphore and wait
                    self.tasks_semaphore.release()
                    await asyncio.sleep(1)
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def _fetch_next_task(self, worker_name: str) -> Optional[TaskQueue]:
        """Fetch next pending task and lock it"""
        try:
            db = SessionLocal()
            
            # Find next pending task (ordered by priority DESC, created_at ASC)
            now = datetime.now(timezone.utc)
            task = db.query(TaskQueue).filter(
                TaskQueue.status == 'pending',
                (TaskQueue.scheduled_for == None) | (TaskQueue.scheduled_for <= now)
            ).order_by(
                TaskQueue.priority.desc(),
                TaskQueue.created_at.asc()
            ).first()
            
            if task:
                # Lock the task
                task.status = 'running'
                task.locked_by = worker_name
                task.locked_at = now
                task.started_at = now
                db.commit()
                db.refresh(task)
                logger.debug(f"Worker {worker_name} locked task {task.id}")
                return task
            
            return None
        except Exception as e:
            logger.error(f"Failed to fetch task: {e}")
            return None
        finally:
            db.close()
    
    async def _execute_task(self, task: TaskQueue, worker_name: str):
        """Execute a task based on its type"""
        try:
            payload = json.loads(task.payload)
            
            # Route to appropriate handler based on task_type
            if task.task_type == 'crawl_domain':
                await self._handle_crawl_task(task.id, payload)
            elif task.task_type == 'extract_contacts':
                await self._handle_extraction_task(task.id, payload)
            elif task.task_type == 'translate_keyword':
                await self._handle_translation_task(task.id, payload)
            else:
                logger.warning(f"Unknown task type: {task.task_type}")
                await self._handle_task_failure(task.id, f"Unknown task type: {task.task_type}")
                return
            
            # Mark as completed
            await self._handle_task_completion(task.id, {"status": "success"})
            logger.info(f"Task {task.id} ({task.task_type}) completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task.id} execution failed: {e}")
            raise
    
    async def _handle_crawl_task(self, task_id: int, payload: Dict):
        """Handle domain crawling task"""
        # Import here to avoid circular imports
        from main import ContactMiningPipeline
        
        keyword_id = payload.get('keyword_id')
        domain = payload.get('domain')
        
        if not keyword_id or not domain:
            raise ValueError("Missing keyword_id or domain in payload")
        
        # Create pipeline instance and run crawl
        pipeline = ContactMiningPipeline()
        await pipeline.initialize()
        
        try:
            result = await pipeline.crawl_single_domain(keyword_id, domain)
            await self._handle_task_completion(task_id, result)
        finally:
            await pipeline.close()
    
    async def _handle_extraction_task(self, task_id: int, payload: Dict):
        """Handle contact extraction task"""
        # Implementation for contact extraction
        logger.info(f"Executing extraction task {task_id}")
        # TODO: Implement extraction logic
        await self._handle_task_completion(task_id, {"status": "extracted"})
    
    async def _handle_translation_task(self, task_id: int, payload: Dict):
        """Handle keyword translation task"""
        from services.translation_service import TranslationService
        
        keyword_id = payload.get('keyword_id')
        keyword_text = payload.get('keyword')
        
        if not keyword_id or not keyword_text:
            raise ValueError("Missing keyword_id or keyword in payload")
        
        translator = TranslationService()
        translations = await translator.translate_to_russian([keyword_text])
        
        await self._handle_task_completion(task_id, {"translations": translations})
    
    async def _handle_task_completion(self, task_id: int, result: Dict):
        """Mark task as completed"""
        try:
            db = SessionLocal()
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if task:
                task.status = 'completed'
                task.result = json.dumps(result)
                task.completed_at = datetime.now(timezone.utc)
                task.locked_by = None
                task.locked_at = None
                db.commit()
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
        finally:
            db.close()
    
    async def _handle_task_failure(self, task_id: int, error_message: str):
        """Handle task failure with retry logic"""
        try:
            db = SessionLocal()
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if task:
                task.retry_count += 1
                task.error_message = error_message
                
                if task.retry_count < task.max_retries:
                    # Retry the task
                    task.status = 'pending'
                    task.locked_by = None
                    task.locked_at = None
                    logger.info(f"Task {task_id} will retry ({task.retry_count}/{task.max_retries})")
                else:
                    # Max retries reached
                    task.status = 'failed'
                    task.completed_at = datetime.now(timezone.utc)
                    task.locked_by = None
                    task.locked_at = None
                    logger.error(f"Task {task_id} failed after {task.retry_count} retries")
                
                db.commit()
        except Exception as e:
            logger.error(f"Failed to handle task failure {task_id}: {e}")
        finally:
            db.close()
    
    async def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        try:
            db = SessionLocal()
            stats = {
                'pending': db.query(TaskQueue).filter(TaskQueue.status == 'pending').count(),
                'running': db.query(TaskQueue).filter(TaskQueue.status == 'running').count(),
                'completed': db.query(TaskQueue).filter(TaskQueue.status == 'completed').count(),
                'failed': db.query(TaskQueue).filter(TaskQueue.status == 'failed').count(),
                'total': db.query(TaskQueue).count(),
                'current_workers': self.current_tasks
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
        finally:
            db.close()
    
    async def clear_completed_tasks(self, older_than_days: int = 7):
        """Clear old completed/failed tasks"""
        try:
            db = SessionLocal()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            
            deleted = db.query(TaskQueue).filter(
                TaskQueue.status.in_(['completed', 'failed']),
                TaskQueue.completed_at < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Cleared {deleted} old tasks from queue")
            return deleted
        except Exception as e:
            logger.error(f"Failed to clear old tasks: {e}")
            return 0
        finally:
            db.close()
