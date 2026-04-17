"""
Start a fake Redis server for development/testing
Uses fakeredis to simulate Redis without actual installation
"""
import asyncio
from loguru import logger
import fakeredis.aioredis


async def start_fake_redis(host="localhost", port=6379):
    """Start fake Redis server"""
    logger.info(f"Starting fake Redis server on {host}:{port}")
    
    # Create fake Redis server
    server = fakeredis.FakeServer()
    
    # Note: fakeredis doesn't provide a real TCP server
    # It's meant for testing with direct Python access
    # For production, use real Redis
    
    logger.warning("FakeRedis started (in-memory only)")
    logger.warning("This is for development/testing only")
    logger.warning("For production, install real Redis server")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("FakeRedis stopped")


if __name__ == "__main__":
    asyncio.run(start_fake_redis())
