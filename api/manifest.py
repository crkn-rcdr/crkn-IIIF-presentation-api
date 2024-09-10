from fastapi import APIRouter,Depends,File,UploadFile,HTTPException,BackgroundTasks,Request,Security
from sqlalchemy.ext.asyncio import AsyncSession
from db_config.sqlalchemy_async_connect import async_get_db
import json
from swift_config.swift_config import get_swift_connection
import os
from dotenv import load_dotenv
import logging
from utils.upload_manifest import upload_manifest
from repository.manifest import ManifestRepository
from utils.slug import get_slug
from Azure_auth.auth import azure_scheme
from Azure_auth.jwt_auth import jwt_auth

# load .env file
load_dotenv()
container_name =  os.getenv("CONTAINER_NAME")
jwt_secret = os.getenv("JWT_SECRET")

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

@router.put("/admin/file",dependencies=[Depends(jwt_auth)])
async def send_manifest(slug:str,request:Request,background_tasks: BackgroundTasks,file:UploadFile = File(...),db:AsyncSession = Depends(async_get_db)):
    message = await upload_manifest(slug,request,background_tasks,file,db)   
    return message

   
@router.put("/file",dependencies=[Security(azure_scheme)])
async def update_manifest(slug:str,request:Request,background_tasks: BackgroundTasks,file:UploadFile = File(...),db:AsyncSession = Depends(async_get_db)):
    message = await upload_manifest(slug,request,background_tasks,file,db)   
    return message



    