import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks,Request,UploadFile,HTTPException
from utils.validator import  Validator
import json
from swift_config.swift_config import get_swift_connection
from utils import back_task
from swiftclient.exceptions import ClientException
import logging

# load .env file
load_dotenv()
container_name =  os.getenv("CONTAINER_NAME")

# Connect to Swift
conn = get_swift_connection()

# load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")

async def upload_manifest(slug:str,request:Request,background_tasks: BackgroundTasks,file:UploadFile ,db:AsyncSession):
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
       # Upload manifest to Swift
        conn.put_object(
                container_name,
                manifest_name,
                contents=content,
            )  
        
        #call a back task to write to database
        iiif_url = str(request.base_url) 
        background_tasks.add_task(back_task.manifest_task,manifest,db,iiif_url,slug)
       
    except json.JSONDecodeError:
        raise HTTPException(status_code=400,detail="Invalid JSON content")
    except ClientException as e:
        logger.error(f"Failed to upload to Swift: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500,detail=f"Failed to upload to Swift")
   
    return  {"message":"Upload successfully","data":manifest}



    