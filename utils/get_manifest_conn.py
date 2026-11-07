from fastapi import HTTPException, Request
import logging
import os
import json
import asyncio
import aiohttp
# import pickle - TODO: add back for production servers
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from swift_config.swift_config import get_swift_connection  # (left as-is, even if unused)
from utils.lifespan_handler import initialize_swift

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
    # Access swift_session, swift_token, and swift_storage_url from app state
    swift_session = getattr(request.app.state, 'swift_session', None)
    if swift_session is None or swift_session.closed:
        swift_session = aiohttp.ClientSession()
        request.app.state.swift_session = swift_session

    swift_token = getattr(request.app.state, 'swift_token', None)
    swift_storage_url = getattr(request.app.state, 'swift_storage_url', None)
    
    if not swift_token or not swift_storage_url:
        try:
            swift_token, swift_storage_url = await initialize_swift()
            request.app.state.swift_token = swift_token
            request.app.state.swift_storage_url = swift_storage_url
        except Exception as auth_err:
            logger.error(f"Failed to authenticate with Swift: {auth_err}")
            raise HTTPException(status_code=503, detail="Storage service temporarily unavailable.")
        
    try:
        manifest_name = f'{manifest_id}/manifest.json'
        file_url = f"{swift_storage_url.rstrip('/')}/{container_name}/{manifest_name}"
        headers = {
            "X-Auth-Token": swift_token,
        }
        
        try:
            resp = await swift_session.get(file_url, headers=headers, ssl=False)
        except (aiohttp.ClientError, asyncio.TimeoutError) as conn_err:
            logger.warning(f"Connection error to Swift ({conn_err}), attempting to re-authenticate and retry...")
            swift_token, swift_storage_url = await initialize_swift()
            request.app.state.swift_token = swift_token
            request.app.state.swift_storage_url = swift_storage_url
            file_url = f"{swift_storage_url.rstrip('/')}/{container_name}/{manifest_name}"
            headers["X-Auth-Token"] = swift_token
            resp = await swift_session.get(file_url, headers=headers, ssl=False)

        async with resp:
            # Handle token expiration
            if resp.status == 401:
                logger.error("Swift token has expired or it is invalid. Re-authenticating...")

                # Re-authenticate and retry
                new_token, new_storage_url = await initialize_swift()
                logger.info(
                    "Swift re-authentication completed. Token exists: %s",
                    bool(new_token)
                )
                # update app.state
                request.app.state.swift_token = new_token
                request.app.state.swift_storage_url = new_storage_url

                # update headers and retry the request
                headers["X-Auth-Token"] = new_token
                file_url = f"{new_storage_url.rstrip('/')}/{container_name}/{manifest_name}"
                logger.info("About to retry Swift GET: %s", file_url)
                
                async with swift_session.get(file_url, headers=headers, ssl=False) as retry_resp:
                    logger.info(
                        "Retry Swift GET status: %s",
                        retry_resp.status
                    )
                    if retry_resp.status == 404:
                        raise HTTPException(status_code=404, detail=f"Manifest not found for manifest Id: {manifest_id}.")
                    
                    if retry_resp.status != 200:
                        logger.error(f"Swift GET unexpected status {retry_resp.status} for {file_url}")
                        raise HTTPException(status_code=502, detail="Upstream storage error.")
                    
                    # 200 OK: parse and return
                    manifest_bytes = await retry_resp.read()
                    try:
                        manifest_data = json.loads(manifest_bytes)
                    except Exception:
                        logger.error("Manifest is not valid JSON")
                        raise HTTPException(status_code=502, detail="Manifest is not valid JSON.")
                    
                    return JSONResponse(content=manifest_data, status_code=200)

            if resp.status == 404:
                raise HTTPException(status_code=404, detail=f"Manifest not found for manifest Id: {manifest_id}.")
            
            if resp.status != 200:
                logger.error(f"Swift GET unexpected status {resp.status} for {file_url}")
                raise HTTPException(status_code=502, detail="Upstream storage error.")
            
            # 200 OK: parse and return
            manifest_bytes = await resp.read()
            try:
                manifest_data = json.loads(manifest_bytes)
            except Exception:
                logger.error("Manifest is not valid JSON")
                raise HTTPException(status_code=502, detail="Manifest is not valid JSON.")
            
            return JSONResponse(content=manifest_data, status_code=200)

    except HTTPException:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError) as conn_err:
        logger.error(f"Storage connection failed: {conn_err}")
        raise HTTPException(status_code=503, detail="Storage service connection failed.")
    except Exception as e:
        logger.error(f"Unexpected error in get_manifest_conn: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error retrieving manifest.")
