from swift_config.swift_config import get_swift_connection
from fastapi import HTTPException,Request
import logging
import os
import json
from swiftclient import ClientException
import pickle
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# Load .env file
load_dotenv()
container_name = os.getenv("CONTAINER_NAME")
# Connect to Swift
conn = get_swift_connection()

#config logger
logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


async def get_manifest_conn(slug:str,request: Request):
    """
    #Retrieve file content from the specified Swift container by filename, and format JSON data.
    

    # Access swift_session, swift_token, and swift_storage_url,redis from app state
    swift_session = request.app.state.swift_session
    swift_token = request.app.state.swift_token
    swift_storage_url = request.app.state.swift_storage_url
    
    if not swift_token or not swift_storage_url:
        raise HTTPException(status_code=401, detail="Authentication is not complete or failed.")
    """
   
    try:
        #Access Swift and Redis objects from the app's state
        redis = request.app.state.redis
        manifest_name = f'{slug}/manifest.json'

        #Check Redis cache
        if (cached_profile := await redis.get(f"manifest_{slug}")) is not None:
            return pickle.loads(cached_profile)
  
        #Fetch from Swift storage
        _,manifest = conn.get_object(container_name, manifest_name)
        manifest_data = json.loads(manifest)

        """
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
                   
                except json.JSONDecodeError:
                    # If not valid JSON, raise an error
                    logger.error("Retrieved content is not valid JSON format.")
                    raise HTTPException(status_code=400, detail="The file content is not valid JSON format.")
        """
        # Cache the manifest in Redis 
        logger.info(f"Caching manifest_{slug} in Redis.")
        await redis.set(f"manifest_{slug}", pickle.dumps(manifest_data))
        return JSONResponse(content=manifest_data, status_code=200)
    
    except Exception as e:
        logger.error(f"Error info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Manifest not found for slug: {slug}.")