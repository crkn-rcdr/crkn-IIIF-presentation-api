from fastapi import APIRouter,Depends,File,UploadFile,Request,Security
from utils.upload_manifest import upload_manifest_backend
from Azure_auth.auth import azure_scheme
from Azure_auth.jwt_auth import jwt_auth
from utils.get_manifest_conn import get_manifest_conn
from fastapi_limiter.depends import RateLimiter



router= APIRouter(
    tags=["Manifest"],
)

@router.get("/manifest/{manifest_id:path}",dependencies=[Depends(RateLimiter(times=25, seconds=60))])
async def get_manifest_by_id(manifest_id:str,request:Request):
    manifest = await get_manifest_conn(manifest_id,request)
    return manifest

@router.put("/admin/file",dependencies=[Depends(jwt_auth)])
async def send_manifest(request:Request,
                        file:UploadFile = File(...)
                        ):
    
    message = await upload_manifest_backend(request,file)   
    return message

@router.put("/file",dependencies=[Security(azure_scheme)])
async def update_manifest(request:Request,
                          file:UploadFile = File(...)
                          
                          ):
    message = await upload_manifest_backend(request,file)   
    return message


   



    