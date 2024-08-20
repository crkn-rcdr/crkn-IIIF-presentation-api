from sqlalchemy.orm import Session
from models.data.presentation_models import AnnotationPage
from sqlalchemy import update,delete,insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession    


class AnnotationPageRepository:
    def __init__(self,sess:AsyncSession):
        self.sess:AsyncSession = sess

  
    async def insert_annotation_page(self, annotation_page: AnnotationPage) -> int:
        try:
            self.sess.add(annotation_page)
            await self.sess.flush() 
        except Exception as e:
            raise RuntimeError(f"Failed to insert a manifest: {e}")
        return annotation_page.annotation_page_id

    async def delete_annotation_page(self,canvas_id:str) ->bool:
        try:
           sql = delete(AnnotationPage).where(AnnotationPage.canvas_id == canvas_id)
           sql.execution_options(synchronize_session="fetch")
           await self.sess.execute(sql)
        except:
            return False
        return True
    
    async def get_annotation_page_id(self,canvas_id:str) -> str:
        try:
            sql = select(AnnotationPage.annotation_page_id).where(AnnotationPage.canvas_id == canvas_id)
            sql.execution_options(synchronize_session="fetch")
            result = await self.sess.execute(sql)
            annotation_page_id = result.scalar_one_or_none()
            return annotation_page_id
        
        except Exception as e:
            raise RuntimeError(f"Failed to get a canvas_id: {e}")
        

    
    