from swift_config.swift_config import get_swift_connection
from fastapi import HTTPException
import logging
import os
import json
from utils.redis import get_redis_client
import pickle
async def get_manifest_conn(slug:str):
    # Obtain Redis client directly
    redis_client = await get_redis_client()
    # Connect to Swift
    conn = get_swift_connection()
    # load .env file
    container_name =  os.getenv("CONTAINER_NAME")
    # load logger which defined in main.py
    logger = logging.getLogger("Presentation_logger")
    manifest_name = f'{slug}/manifest.json'
    if (cached_profile := await redis_client.get(f"manifest_{slug}")) is not None:
        return pickle.loads(cached_profile)
    try:
        _,manifest = conn.get_object(container_name, manifest_name)
        manifest_data = json.loads(manifest)
        # Cache the manifest in Redis and ensure the operation is awaited
        await redis_client.set(f"manifest_{slug}", pickle.dumps(manifest_data))
        return manifest_data
    except Exception as e:
        logger.error(f"Error info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Manifest not found")