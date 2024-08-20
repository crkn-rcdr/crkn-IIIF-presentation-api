from fastapi import APIRouter,HTTPException,Depends
import json
from swift_config.swift_config import get_swift_connection
import os
from dotenv import load_dotenv
import logging
from repository.canvas import CanvasRepository
from sqlalchemy.ext.asyncio import AsyncSession
from db_config.sqlalchemy_async_connect import async_get_db
from utils.slug import get_slug
# load .env file
load_dotenv()
container_name =  os.getenv("CONTAINER_NAME")

# load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")
router= APIRouter(
    tags=["Canvas"],
)
# Connect to Swift
conn = get_swift_connection()

@router.get("/canvas/{canvas_id:path}")
async def get_canvas(canvas_id:str,db:AsyncSession = Depends(async_get_db)):
    canvas_repo = CanvasRepository(db)
    try:
        slug = await get_slug(canvas_repo,canvas_id)
        canvas_name = f'{slug}/{canvas_id}/canvas.json'
        _,canvas = conn.get_object(container_name, canvas_name)
        if not canvas:
            raise HTTPException(status_code=404, detail="Canvas is empty")  
        canvas_data = json.loads(canvas)
        return canvas_data
    except Exception as e:
        logger.error(f"JSON decoding error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Internal Server error")
        

 
        