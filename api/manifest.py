from fastapi import APIRouter,Depends,File,UploadFile,Request
from utils.upload_manifest import upload_manifest_backend

from Azure_auth.jwt_auth import jwt_auth
from utils.get_manifest_conn import get_manifest_conn



router= APIRouter(
    tags=["Manifest"],
)

@router.get("/manifest/{manifest_id:path}")
async def get_manifest_by_id(manifest_id:str,request:Request):
    manifest = await get_manifest_conn(manifest_id,request)
    return manifest

@router.put("/admin/file",dependencies=[Depends(jwt_auth)])
async def send_manifest(request:Request,
                        file:UploadFile = File(...)
                        ):
    
    message = await upload_manifest_backend(request,file)   
    return message

   



    