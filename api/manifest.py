from fastapi import APIRouter,Depends,File,UploadFile,HTTPException,BackgroundTasks,Request,Security
from sqlalchemy.ext.asyncio import AsyncSession
from db_config.sqlalchemy_async_connect import async_get_db
import json
from utils.validator import  Validator
from swift_config.swift_config import get_swift_connection
import os
from dotenv import load_dotenv
from swiftclient.exceptions import ClientException
import logging
from utils import back_task
from repository.manifest import ManifestRepository
from utils.slug import get_slug
from Azure_auth.auth import azure_scheme
# load .env file
load_dotenv()
container_name =  os.getenv("CONTAINER_NAME")

# load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")

router= APIRouter(
    tags=["Manifest"],
)
# Connect to Swift
conn = get_swift_connection()
@router.get("/manifest/{manifest_id:path}")
async def get_manifest(manifest_id:str,db:AsyncSession = Depends(async_get_db)):
    manifest_repo = ManifestRepository(db)
    try:
        slug = await get_slug(manifest_repo,manifest_id)
        print(slug,'tet')
        manifest_name = f'{slug}/manifest.json'
        _,manifest = conn.get_object(container_name, manifest_name)
        manifest_data = json.loads(manifest)
        return manifest_data
    except Exception as e:
        logger.error(f"Error info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Manifest not found")
    
@router.put("/file",dependencies=[Security(azure_scheme)])
async def update_manifest(slug:str,request:Request,background_tasks: BackgroundTasks,file:UploadFile = File(...),db:AsyncSession = Depends(async_get_db)):
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
        
        #write to database
        iiif_url = str(request.base_url) 
        background_tasks.add_task(back_task.manifest_task,manifest,db,iiif_url,slug)
       
    except json.JSONDecodeError:
        raise HTTPException(status_code=400,detail="Invalid JSON content")
    except ClientException as e:
        logger.error(f"Failed to upload to Swift: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500,detail=f"Failed to upload to Swift")
   
    return  {"message":"Upload successfully","data":manifest}



    