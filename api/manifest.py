from fastapi import APIRouter,Depends,File,UploadFile,Request,Security,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db_config.sqlalchemy_async_connect import async_get_db
from utils.upload_manifest import upload_manifest_backend
from repository.manifest import ManifestRepository
from utils.slug import get_slug
from Azure_auth.auth import azure_scheme
from Azure_auth.jwt_auth import jwt_auth
from utils.get_manifest_conn import get_manifest_conn



router= APIRouter(
    tags=["Manifest"],
)

@router.get("/manifest/slug/{slug}")
async def get_manifest_by_slug(slug:str,request:Request):
    manifest = await get_manifest_conn(slug,request)
    return manifest   

@router.get("/manifest/{manifest_id:path}")
async def get_manifest_by_id(manifest_id:str,request:Request,db:AsyncSession = Depends(async_get_db)):
    manifest_repo = ManifestRepository(db)
    slug = await get_slug(manifest_repo,manifest_id)
    manifest = await get_manifest_conn(slug,request)
    return manifest


@router.put("/admin/file",dependencies=[Depends(jwt_auth)])
async def send_manifest(slug:str,
                        request:Request,
                        file:UploadFile = File(...),
                        db:AsyncSession = Depends(async_get_db)
                        ):
    
    message = await upload_manifest_backend(slug,request,file,db)   
    return message

   
@router.put("/file",dependencies=[Security(azure_scheme)])
async def update_manifest(slug:str,
                          request:Request,
                          file:UploadFile = File(...),
                          db:AsyncSession = Depends(async_get_db)
                          ):
    message = await upload_manifest_backend(slug,request,file,db)   
    return message



    