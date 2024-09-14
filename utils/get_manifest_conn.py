from swift_config.swift_config import get_swift_connection
from fastapi import HTTPException
import logging
import os
import json
async def get_manifest_conn(slug:str):
    # Connect to Swift
    conn = get_swift_connection()
    # load .env file
    container_name =  os.getenv("CONTAINER_NAME")
    # load logger which defined in main.py
    logger = logging.getLogger("Presentation_logger")
    try:
        manifest_name = f'{slug}/manifest.json'
        _,manifest = conn.get_object(container_name, manifest_name)
        manifest_data = json.loads(manifest)
        return manifest_data
    except Exception as e:
        logger.error(f"Error info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Manifest not found")