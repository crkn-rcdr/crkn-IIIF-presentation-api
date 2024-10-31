import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, UploadFile, HTTPException
from utils.validator import Validator
import json
from utils import back_task
from redis.asyncio import Redis
from contextlib import asynccontextmanager
import logging
from urllib.parse import urlparse
import botocore

# Load .env file
load_dotenv()
container_name = os.getenv("CONTAINER_NAME")
#config logger
logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


# Create an async context manager for acquiring and releasing a Redis lock
@asynccontextmanager
async def acquire_lock(redis_client: Redis, key: str, timeout: int = 30):
    lock_acquired = await redis_client.set(key, "locked", nx=True, ex=timeout)
    try:
        if not lock_acquired:
            raise HTTPException(status_code=409, detail="Manifest is being updated, please try again later.")
        yield
    finally:
        await redis_client.delete(key)

async def upload_manifest_backend(
    request: Request,
    file: UploadFile,
    db: AsyncSession
):
    # Access swift_session, swift_token, and swift_storage_url from app state
   
    swift_session = request.app.state.swift_session
    swift_token = request.app.state.swift_token
    swift_storage_url = request.app.state.swift_storage_url
    
    redis = request.app.state.redis
    
   
    
    if not swift_token:
        raise HTTPException(status_code=401, detail="Swift authentication token not found.")
   
    try:
        try:
            content = await file.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise HTTPException(status_code=500, detail="Failed to read the uploaded file.")
        manifest = json.loads(content)
        try:
            slug_value_dict = manifest['metadata'][0]['value']
            slug = list(slug_value_dict.values())[0][0]
        except Exception as e:
            logger.error(f"Error extracting slug from manifest: {e}")
            raise HTTPException(status_code=400, detail="Invalid manifest structure: missing slug.")
        
        # Define the Redis lock key based on the slug
        lock_key = f"lock_manifest_{slug}"

        # Use the acquire_lock context manager to ensure exclusive access
        async with acquire_lock(redis, lock_key):
            # Check if a file is uploaded
            if not file or file.filename == "":
                raise HTTPException(status_code=400, detail="No file uploaded. Please upload a file.")
            # Verify file format
            if file.content_type != "application/json":
                raise HTTPException(status_code=400, detail="Invalid file type. Only JSON files are allowed.")
         
            if not content:
                raise HTTPException(status_code=400, detail="Empty file is not allowed.")
    
            # Validate the manifest, pass JSON string
            validator = Validator()
            result = json.loads(validator.check_manifest(content))
            if result['okay'] == 0:
                raise HTTPException(
        status_code=400,
        detail={
            "message": "The manifest is invalid. Please correct it based on the provided error information.",
            "data": {
                "error": result['error'],
                "errorList": result['errorList']
            }
        }
    )

            manifest_name = f'{slug}/manifest.json'
            parsed_url = urlparse(manifest['id'])
            base_url = str(request.base_url)
            manifest_id = f"{base_url.rstrip('/')}{parsed_url.path}"
            manifest['id']=manifest_id
            
            # Check for empty values and raise error if any are found
            empty_keys = [key for key, value in manifest.items() if not value]
            if empty_keys:
                raise HTTPException(
                    status_code=400,
                    detail=f"The following keys have empty values: {empty_keys}. Please provide values or remove the keys."
                )
            canvas_content = manifest['items']
            new_manifest_items = []
            #extract canvas values to upload files to swift
            for canvas_item in canvas_content:
                
                canvas_id = "/".join(canvas_item['id'].split("/")[-2:])
                #canvas_name = f'{slug}/{canvas_id}/canvas.json'
                canvas_parsed_url = urlparse(canvas_item['id'])
                target_parsed_url = urlparse(canvas_item['items'][0]['items'][0]['target'])
                annotation_page_parsed_url = urlparse(canvas_item['items'][0]['id'])
                annotation_parsed_url = urlparse(canvas_item['items'][0]['items'][0]['id'])
                canvas_id = f"{base_url.rstrip('/')}{canvas_parsed_url.path}"
                target = f"{base_url.rstrip('/')}{target_parsed_url.path}"
                annotation_page_id = f"{base_url.rstrip('/')}{annotation_page_parsed_url.path}"
                annotation_id = f"{base_url.rstrip('/')}{annotation_parsed_url.path}"
                canvas_item['id']=canvas_id
                canvas_item['items'][0]['items'][0]['target'] = target
                canvas_item['items'][0]['id'] = annotation_page_id
                canvas_item['items'][0]['items'][0]['id'] = annotation_id
                new_manifest_items.append(canvas_item)
                #updated_canvas_content = json.dumps(canvas_item)
            # Upload manifest to Swift
            manifest['items'] = new_manifest_items
            updated_manifest = json.dumps(manifest)
            upload_url = f"{swift_storage_url}/{container_name}/{manifest_name}"
            headers = {
            "X-Auth-Token": swift_token,
            "Content-Type": "application/json"
            }
            async with swift_session.put(upload_url,headers=headers,data=updated_manifest,ssl=False) as resp:
                if resp.status not in (201, 202, 204):
                    text = await resp.text() 
                    logger.info(f"File upload failed: {text}")       
                    raise HTTPException(status_code=resp.status, detail=f"File upload failed")         
            
            # Check cache and delete if it exists
            redis_key = f"manifest_{slug}"
            if (await redis.get(redis_key)) is not None:
                await redis.delete(redis_key)

            # write to the database
            iiif_url = str(request.base_url)
            await back_task.manifest_task (manifest,db,iiif_url,slug_value_dict)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON content")
    
    except botocore.exceptions.BotoCoreError as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed")
    
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise e

    return {"message": "Upload successfully", "data": manifest}
