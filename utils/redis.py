from redis.asyncio import Redis
from dotenv import load_dotenv
import os

async def get_redis_client():
    # Load .env file
    load_dotenv()
    # Get Redis server and port from environment variables
    redis_server = os.getenv("REDIS_SERVER", "redis-cache")
    redis_port = os.getenv("REDIS_PORT", "6379")
    # Create an asynchronous Redis client
    redis_client = await Redis.from_url(
        f"redis://{redis_server}:{redis_port}/0",
        encoding="utf-8",
        decode_responses=False,
        ssl=True
    )
    return redis_client
