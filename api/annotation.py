from fastapi import APIRouter,HTTPException,Request,Depends
import json
from swift_config.swift_config import get_swift_connection
import os
from dotenv import load_dotenv
from swiftclient.exceptions import ClientException
import logging
from db_config.sqlalchemy_async_connect import async_get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.slug import get_slug
from repository.canvas import CanvasRepository
# load .env file
load_dotenv()
container_name =  os.getenv("CONTAINER_NAME")

# load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")

router= APIRouter(
    tags=["Annotation"],
)
# Connect to Swift
conn = get_swift_connection()
@router.get("/{manifest_id:path}/annotation/{canvas_id:path}/main/image")
async def get_annotation(manifest_id:str,canvas_id:str,request:Request,db:AsyncSession = Depends(async_get_db)):
    full_path = request.url.path
    annotation_suffix = full_path.split('/annotation/')[1]
    canvas_repo = CanvasRepository(db)
    slug = await get_slug(canvas_repo,canvas_id)
    try:
        annotation_name = f'{slug}/{manifest_id}/{annotation_suffix}/annotation.json'

        _,annotation = conn.get_object(container_name, annotation_name)
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation is empty")
        annotation_data = json.loads(annotation)
        
    except ClientException as e:
        logger.error(f"Swift Client error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Annotation not found")
    return annotation_data 
  