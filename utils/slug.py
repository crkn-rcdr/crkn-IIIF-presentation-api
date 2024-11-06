from fastapi import HTTPException
import logging
from utils.metadata_slug import get_slug_in_metadata

#config logger
logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

async def get_slug(repo,id):
     try:
        _metadata = await repo.get_slug(id)
        if _metadata is None :
            raise HTTPException(status_code=404, detail=f"Slug not found for the associated ID: {id}")
        slug =  get_slug_in_metadata(_metadata)[0]
        return slug
     except Exception as e:
        logger.error(f"Failed to get the slug: {e}")
        raise HTTPException(status_code=404, detail=f"Slug not found for the associated ID: {id}")