import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks,Request,UploadFile,HTTPException,Depends
from utils.validator import  Validator
import json
from swift_config.swift_config import get_swift_connection
from utils import back_task
from swiftclient.exceptions import ClientException
import logging
from utils.redis import get_redis_client

# load .env file
load_dotenv()
container_name =  os.getenv("CONTAINER_NAME")

# Connect to Swift
conn = get_swift_connection()

# load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")

async def upload_manifest(slug:str,
                          request:Request,
                          background_tasks: BackgroundTasks,
                          file:UploadFile ,db:AsyncSession,
                          redis_client):
     #verify file format
    if file.content_type != "application/json":
        raise HTTPException(status_code=400,detail="Invalid file typ. Only JSON files are allowed.")
    try:
        content = await file.read()
        # Validate the manifest,pass JSON string
        validator = Validator()
        result = json.loads(validator.check_manifest(content))
        if result['okay'] == 0:
            return {"message":"The manifest is invalid. Please correct it based on the provided error information.",
                    "data":{"error":result['error'],"errorList":result['errorList']}
                    }
        manifest = json.loads(content)
        #manifest_id = "/".join(manifest['id'].split('/')[-2:])
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
        
        #call a back task to write to database
        iiif_url = str(request.base_url) 
        background_tasks.add_task(back_task.manifest_task,manifest,db,iiif_url,slug)
       
    except json.JSONDecodeError:
        raise HTTPException(status_code=400,detail="Invalid JSON content")
    except ClientException as e:
        logger.error(f"Failed to upload to Swift: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500,detail=f"Failed to upload to Swift")
   
    return  {"message":"Upload successfully","data":manifest}



    