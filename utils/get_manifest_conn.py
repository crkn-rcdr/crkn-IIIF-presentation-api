
from fastapi import HTTPException,Request
import logging
import os
import json
import pickle
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from swift_config.swift_config import get_swift_connection

# Load .env file
load_dotenv()
container_name = os.getenv("CONTAINER_NAME")

#config logger
logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

async def get_manifest_conn(manifest_id:str,request: Request):
    """
    Retrieve file content from the specified Swift container by filename, and format JSON data.
    """
    #Access swift_session, swift_token, and swift_storage_url,redis from app state
    swift_session = request.app.state.swift_session
    swift_token = request.app.state.swift_token
    swift_storage_url = request.app.state.swift_storage_url
    
    if not swift_token or not swift_storage_url:
        raise HTTPException(status_code=401, detail="Authentication is not complete or failed.")
    
    #Check Redis cache,if exists return from redis otherwise is None or get an error continue to get data from swift
    cached_profile = None
    try:
        #Access Swift and Redis objects from the app's state
        redis = request.app.state.redis
        #conn = request.app.state.conn
        cached_profile = await redis.get(f"manifest_{manifest_id}")
    except Exception as redis_err:
        logger.error(f"Redis error: {redis_err}")
    
    try:
        if cached_profile is not None:
            return pickle.loads(cached_profile)
    except Exception as e:
        logger.error(f"Pickle error: {str(e)}", exc_info=True)
        
    try:
        manifest_name = f'{manifest_id}/manifest.json'
        # retrieve from the container
        file_url = f"{swift_storage_url}/{container_name}/{manifest_name}"
        headers = {
            "X-Auth-Token": swift_token
        }
        
        async with swift_session.get(file_url,headers=headers,ssl=False) as resp:
            #Handle token expiration
            if resp.status == 401:
                logger.error("Swift token has expired or it invalid.")
                raise HTTPException(status_code=401,detail="Swift token has expired. Please re-authenticate.")
            
            if resp.status == 200:    
                manifest = await resp.read()
                manifest_data = json.loads(manifest)     
        #_,manifest = conn.get_object(container_name, manifest_name)
        #manifest_data = json.loads(manifest)
        # Cache the manifest in Redis 
        logger.info(f"Caching manifest_{manifest_id} in Redis.")
        await redis.set(f"manifest_{manifest_id}", pickle.dumps(manifest_data))
        return JSONResponse(content=manifest_data, status_code=200)
    
    except Exception as e:
        logger.error(f"Error info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Manifest not found for manifest Id: {manifest_id}.")
