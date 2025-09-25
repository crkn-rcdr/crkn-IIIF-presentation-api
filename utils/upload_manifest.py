import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, UploadFile, HTTPException
from utils.validator import Validator
import json
# from redis.asyncio import Redis - TODO: add back for production servers
from contextlib import asynccontextmanager
import logging
import botocore.exceptions
from swift_config.swift_config import get_swift_connection
from utils.settings import container_name

#config logger
logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Create an async context manager for acquiring and releasing a Redis lock
# @asynccontextmanager
# async def acquire_lock(redis_client: Redis, key: str, timeout: int = 30):
#     lock_acquired = await redis_client.set(key, "locked", nx=True, ex=timeout)
#     try:
#         if not lock_acquired:
#             raise HTTPException(status_code=409, detail="Manifest is being updated, please try again later.")
#         yield
#     finally:
#         await redis_client.delete(key)

async def upload_manifest_backend(
    request: Request,
    file: UploadFile,
):
    swift_session = request.app.state.swift_session
    swift_token = request.app.state.swift_token
    swift_storage_url = request.app.state.swift_storage_url

    if not swift_token:
        raise HTTPException(status_code=401, detail="Swift authentication token not found.")

    try:
        try:
            content = await file.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise HTTPException(status_code=500, detail="Failed to read the uploaded file.")

        # basic request checks
        if not file or file.filename == "":
            raise HTTPException(status_code=400, detail="No file uploaded. Please upload a file.")
        if file.content_type != "application/json":
            raise HTTPException(status_code=400, detail="Invalid file type. Only JSON files are allowed.")
        if not content:
            raise HTTPException(status_code=400, detail="Empty file is not allowed.")

        # parse and validate
        manifest = json.loads(content)
        manifest_id = "/".join(manifest['id'].split('/')[-2:])

        validator = Validator()
        result = json.loads(validator.check_manifest(content))
        if result['okay'] == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "The manifest is invalid. Please correct it based on the provided error information.",
                    "data": {
                        "error": result['error'],
                        "errorList": result['errorList'],
                    },
                },
            )

        # ---- FROM HERE ON: this must run when validation passed (FIXED INDENTATION) ----
        manifest_name = f"{manifest_id}/manifest.json"

        # optional: reject empty values
        empty_keys = [key for key, value in manifest.items() if not value]
        if empty_keys:
            raise HTTPException(
                status_code=400,
                detail=f"The following keys have empty values: {empty_keys}. Please provide values or remove the keys.",
            )

        # upload to Swift via tokenized HTTP
        updated_manifest = json.dumps(manifest, ensure_ascii=False)
        upload_url = f"{swift_storage_url.rstrip('/')}/{container_name}/{manifest_name}"
        headers = {
            "X-Auth-Token": swift_token,
            "Content-Type": "application/json",
        }

        async with swift_session.put(upload_url, headers=headers, data=updated_manifest, ssl=False) as resp:
            # OpenStack Swift usually returns 201 for object PUT; accept a few success codes
            if resp.status not in (200, 201, 202, 204):
                text = await resp.text()
                logger.info(f"File upload failed [{resp.status}]: {text}")
                raise HTTPException(status_code=resp.status, detail="File upload failed")

            # log success for debugging
            logger.info(f"Uploaded manifest to {upload_url} (status {resp.status})")

        # (optional) cache invalidation here...

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON content")
    except botocore.exceptions.BotoCoreError as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        raise e

    return {"message": "Upload successfully!"}
