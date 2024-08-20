from fastapi import APIRouter,HTTPException,Depends,Request
import json
from swift_config.swift_config import get_swift_connection
import os
from dotenv import load_dotenv
from swiftclient.exceptions import ClientException
import logging
from utils.slug import get_slug
from repository.canvas import CanvasRepository
from db_config.sqlalchemy_async_connect import async_get_db
from sqlalchemy.ext.asyncio import AsyncSession
# load .env file
load_dotenv()
container_name =  os.getenv("CONTAINER_NAME")

# load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")

router= APIRouter(
    tags=["Annotation Page"],
)
# Connect to Swift
conn = get_swift_connection()
@router.get("/{manifest_id:path}/annotationpage/{canvas_id:path}/main")
async def get_annotation_page(manifest_id: str, canvas_id: str, request: Request, db: AsyncSession = Depends(async_get_db)):
    full_path = request.url.path
    annotation_page_suffix = full_path.split(canvas_id)[1]
    canvas_repo = CanvasRepository(db)
    slug = await get_slug(canvas_repo,canvas_id)
    annotation_page_name = f'{slug}/{canvas_id}/{manifest_id}{annotation_page_suffix}/annotation_page.json'
    try:
        _,annotation_page = conn.get_object(container_name, annotation_page_name)
        if not annotation_page:
            raise HTTPException(status_code=404, detail="Annotation page is empty")
        annotation_page_data = json.loads(annotation_page)
    except ClientException as e:
        logger.error(f"Swift Client error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail="Annotation page not found")
    return annotation_page_data
