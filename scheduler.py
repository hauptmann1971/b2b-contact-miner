import schedule
import time
import asyncio
from loguru import logger
from main import ContactMiningPipeline


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
    start_scheduler()
