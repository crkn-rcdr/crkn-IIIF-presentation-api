import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, UploadFile, HTTPException
from utils.validator import Validator
import json
from swift_config.swift_config import get_swift_connection
from utils import back_task
from swiftclient.exceptions import ClientException
import logging
from utils.redis import get_redis_client
from redis.asyncio import Redis
from contextlib import asynccontextmanager

# Load .env file
load_dotenv()
container_name = os.getenv("CONTAINER_NAME")

# Connect to Swift
conn = get_swift_connection()

# Load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")

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
            conn.put_object(
                container_name,
                manifest_name,
                contents=content,
            )

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
            logger.error(f"Failed to upload to Swift: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to upload to Swift")

    return {"message": "Upload successfully", "data": manifest}
