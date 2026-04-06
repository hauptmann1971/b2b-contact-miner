import asyncio
from asyncio import Queue
from typing import Callable, Any
from loguru import logger
from datetime import datetime


class AsyncTaskQueue:
    """Async task queue using asyncio.Queue instead of Celery"""
    
    def __init__(self, max_concurrent: int = 20):
        self.queue = Queue(maxsize=1000)
        self.max_concurrent = max_concurrent
        self.workers = []
        self.running = False
    
    async def start_workers(self):
        """Start worker tasks"""
        self.running = True
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        logger.info(f"Started {self.max_concurrent} async workers")
    
    async def stop_workers(self):
        """Stop all workers gracefully"""
        self.running = False
        await self.queue.join()
        
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("All workers stopped")
    
    async def add_task(self, coro_func: Callable, *args, **kwargs):
        """Add task to queue"""
        await self.queue.put((coro_func, args, kwargs))
    
    async def _worker(self, worker_id: int):
        """Worker that processes tasks from queue"""
        while self.running:
            try:
                coro_func, args, kwargs = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
                
                try:
                    await coro_func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Worker {worker_id} task failed: {e}")
                finally:
                    self.queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
