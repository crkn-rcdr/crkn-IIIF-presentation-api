import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, UploadFile, HTTPException
from utils.validator import Validator
import json
from utils import back_task
from swiftclient.exceptions import ClientException
from redis.asyncio import Redis
from contextlib import asynccontextmanager
import logging

# Load .env file
load_dotenv()
container_name = os.getenv("CONTAINER_NAME")
#config logger
logging.basicConfig(level=logging.INFO)
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

async def upload_manifest(
    slug: str,
    request: Request,
    file: UploadFile,
    db: AsyncSession,
    redis_client: Redis
):
    # Access swift_session, swift_token, and swift_storage_url from app state
    swift_session = request.app.state.swift_session
    swift_token = request.app.state.swift_token
    swift_storage_url = request.app.state.swift_storage_url

    if not swift_token:
        raise HTTPException(status_code=401, detail="Swift authentication token not found.")
    # Define the Redis lock key based on the slug
    lock_key = f"lock_manifest_{slug}"

    # Use the acquire_lock context manager to ensure exclusive access
    async with acquire_lock(redis_client, lock_key):
        # Check if a file is uploaded
        if file is None or file.filename == "":
            raise HTTPException(status_code=400, detail="No file uploaded. Please upload a JSON file.")
        # Verify file format
        if file.content_type != "application/json":
            raise HTTPException(status_code=400, detail="Invalid file type. Only JSON files are allowed.")
        try:
            content = await file.read()
            if content is None:
                raise HTTPException(status_code=400, detail="Empty file is not allowed")
            # Validate the manifest, pass JSON string
            validator = Validator()
            result = json.loads(validator.check_manifest(content))
            if result['okay'] == 0:
                return {
                    "message": "The manifest is invalid. Please correct it based on the provided error information.",
                    "data": {"error": result['error'], "errorList": result['errorList']}
                }

            manifest = json.loads(content)
            manifest_name = f'{slug}/manifest.json'

            # Check for empty values and raise error if any are found
            empty_keys = [key for key, value in manifest.items() if not value]
            if empty_keys:
                raise HTTPException(
                    status_code=400,
                    detail=f"The following keys have empty values: {empty_keys}. Please provide values or remove the keys."
                )

            # Upload manifest to Swift
            upload_url = f"{swift_storage_url}/{container_name}/{manifest_name}"
            headers = {
            "X-Auth-Token": swift_token,
            "Content-Type": "application/json"
            }
            async with swift_session.put(upload_url,headers=headers,data=content,ssl=False) as resp:
                if resp.status not in (201, 202, 204):
                    text = await resp.text() 
                    logger.info(f"File upload failed: {text}")       
                    raise HTTPException(status_code=resp.status, detail=f"File upload failed")         

            # Check cache and delete if it exists
            redis_key = f"manifest_{slug}"
            if (await redis_client.get(redis_key)) is not None:
                await redis_client.delete(redis_key)

            # write to the database
            iiif_url = str(request.base_url)
            await back_task.manifest_task (manifest,db,iiif_url, slug)

        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON content")
        except ClientException as e:
           
            raise HTTPException(status_code=500, detail="Failed to upload to Swift")

    return {"message": "Upload successfully", "data": manifest}
