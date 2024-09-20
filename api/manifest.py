from fastapi import APIRouter,Depends,File,UploadFile,BackgroundTasks,Request,Security
from sqlalchemy.ext.asyncio import AsyncSession
from db_config.sqlalchemy_async_connect import async_get_db
from swift_config.swift_config import get_swift_connection
from utils.upload_manifest import upload_manifest
from repository.manifest import ManifestRepository
from utils.slug import get_slug
from Azure_auth.auth import azure_scheme
from Azure_auth.jwt_auth import jwt_auth
from utils.get_manifest_conn import get_manifest_conn
from utils.redis import get_redis_client


router= APIRouter(
    tags=["Manifest"],
)

@router.get("/manifest/manifest_id/{manifest_id:path}")
async def get_manifest_by_id(manifest_id:str,db:AsyncSession = Depends(async_get_db)):
    manifest_repo = ManifestRepository(db)
    slug = await get_slug(manifest_repo,manifest_id)
    manifest = await get_manifest_conn(slug)
    return manifest

@router.get("/manifest/slug/{slug}")
async def get_manifest_by_slug(slug:str):
    manifest = await get_manifest_conn(slug)
    return manifest      

@router.put("/admin/file",dependencies=[Depends(jwt_auth)])
async def send_manifest(slug:str,request:Request,background_tasks: BackgroundTasks,file:UploadFile = File(...),db:AsyncSession = Depends(async_get_db)):
    message = await upload_manifest(slug,request,background_tasks,file,db)   
    return message

   
@router.put("/file",dependencies=[Security(azure_scheme)])
async def update_manifest(slug:str,request:Request,
                          background_tasks: BackgroundTasks,
                          file:UploadFile = File(...),
                          db:AsyncSession = Depends(async_get_db),
                          redis_client = Depends(get_redis_client)):
    message = await upload_manifest(slug,request,background_tasks,file,db,redis_client)   
    return message



    