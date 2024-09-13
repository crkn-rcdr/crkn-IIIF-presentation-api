from models.data.presentation_models import Annotation
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession    
class AnnotationRepository:
    def __init__(self,sess:AsyncSession):
        self.sess:AsyncSession = sess

    async def insert_annotation(self,annotation:Annotation) -> bool:
        try:
            self.sess.add(annotation)
            await self.sess.flush() 
        except Exception as e:
            raise RuntimeError(f"Failed to insert a manifest: {e}")
        return True

    async def delete_annotation(self,annotation_page_id:str) ->bool:
        try:
           sql = delete(Annotation).where(Annotation.annotation_page_id == annotation_page_id)
           sql.execution_options(synchronize_session="fetch")
           await self.sess.execute(sql)
        except:
            return False
        return True
