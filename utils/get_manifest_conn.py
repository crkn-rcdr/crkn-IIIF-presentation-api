from swift_config.swift_config import get_swift_connection
from fastapi import HTTPException,Request
import logging
import os
import json
from utils.redis import get_redis_client
import pickle
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# Load .env file
load_dotenv()
container_name = os.getenv("CONTAINER_NAME")

#config logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_manifest_conn(slug:str,request: Request):
    """
    Retrieve file content from the specified Swift container by filename, and format JSON data.
    """
    # Obtain Redis client directly
    redis_client = await get_redis_client()
    # Access swift_session, swift_token, and swift_storage_url from app state
    swift_session = request.app.state.swift_session
    swift_token = request.app.state.swift_token
    swift_storage_url = request.app.state.swift_storage_url
    if not swift_token or not swift_storage_url:
        raise HTTPException(status_code=401, detail="Authentication is not complete or failed.")
    manifest_name = f'{slug}/manifest.json'
    if (cached_profile := await redis_client.get(f"manifest_{slug}")) is not None:
        return pickle.loads(cached_profile)
    try:
        file_url = f"{swift_storage_url}/{container_name}/{manifest_name}"
        headers = {
            "X-Auth-Token": swift_token
        }
        async with swift_session.get(file_url,headers=headers,ssl=False) as resp:
            if resp.status == 200:
                manifest = await resp.read()
                try:
                    # Attempt to parse the data as JSON
                    manifest_data = json.loads(manifest.decode('utf-8'))
                    # Properly format the JSON with indentation
                    return JSONResponse(content=manifest_data, status_code=200)
                except json.JSONDecodeError:
                    # If not valid JSON, raise an error
                    logger.error("Retrieved content is not valid JSON format.")
                    raise HTTPException(status_code=400, detail="The file content is not valid JSON format.")
        # Cache the manifest in Redis and ensure the operation is awaited
        await redis_client.set(f"manifest_{slug}", pickle.dumps(manifest_data))
        return manifest_data
    except Exception as e:
        logger.error(f"Error info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Manifest not found")