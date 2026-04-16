"""Test script to add tasks to database queue"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workers.db_task_queue import DatabaseTaskQueue
from loguru import logger

async def test_queue():
    """Add test tasks to queue"""
    logger.info("Initializing task queue...")
    
    # Create task queue
    queue = DatabaseTaskQueue(max_concurrent=5)
    await queue.start_workers()
    
    # Register queue with monitoring healthcheck
    try:
        import monitoring.healthcheck as health_module
        health_module.task_queue = queue
        logger.info("✓ Queue registered with monitoring")
    except Exception as e:
        logger.warning(f"Failed to register with monitoring: {e}")
    
    logger.info("Adding test tasks...")
    
    # Add some test tasks
    test_tasks = [
        {
            "task_name": f"test_crawl_{i}",
            "task_type": "crawl_domain",
            "payload": {"url": f"https://example{i}.com"},
            "priority": i
        }
        for i in range(1, 6)
    ]
    
    for task_data in test_tasks:
        task_id = await queue.add_task(
            task_name=task_data["task_name"],
            task_type=task_data["task_type"],
            payload=task_data["payload"],
            priority=task_data["priority"]
        )
        logger.info(f"✓ Added task {task_id}: {task_data['task_name']}")
    
    logger.info("\nWaiting 3 seconds for workers to process...")
    await asyncio.sleep(3)
    
    # Get stats
    stats = await queue.get_queue_stats()
    logger.info(f"\n📊 Queue Statistics:")
    logger.info(f"   Pending: {stats.get('pending', 0)}")
    logger.info(f"   Running: {stats.get('running', 0)}")
    logger.info(f"   Completed: {stats.get('completed', 0)}")
    logger.info(f"   Failed: {stats.get('failed', 0)}")
    logger.info(f"   Total: {stats.get('total', 0)}")
    
    await queue.stop_workers()
    logger.info("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_queue())
