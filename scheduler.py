import schedule
import time
import asyncio
import os
from loguru import logger
from main import ContactMiningPipeline


def write_pid_file():
    """Write current process ID to file"""
    pid_dir = 'pids'
    os.makedirs(pid_dir, exist_ok=True)
    pid_file = os.path.join(pid_dir, 'scheduler.pid')
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"PID file created: {pid_file} (PID: {os.getpid()})")


def run_daily_pipeline():
    """Run the contact mining pipeline"""
    logger.info("Scheduled pipeline run started")
    
    try:
        pipeline = ContactMiningPipeline()
        asyncio.run(pipeline.run_pipeline())
        logger.info("Scheduled pipeline run completed")
    except Exception as e:
        logger.error(f"Scheduled pipeline failed: {e}")


def start_scheduler():
    """Start the cron scheduler"""
    schedule.every().day.at("02:00").do(run_daily_pipeline)
    
    logger.info("Scheduler started - pipeline will run daily at 02:00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    write_pid_file()
    start_scheduler()
