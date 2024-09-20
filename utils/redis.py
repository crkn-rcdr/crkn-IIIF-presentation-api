from redis.asyncio import Redis
from dotenv import load_dotenv
import os

async def get_redis_client():
    # Load .env file
    load_dotenv()
    # Create an asynchronous Redis client
    redis_client = await Redis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=False
    )
    return redis_client
