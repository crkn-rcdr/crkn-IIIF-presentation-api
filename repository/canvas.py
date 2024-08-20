
from models.data.presentation_models import Canvas,Manifest
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession    

class CanvasRepository:
    def __init__(self,sess:AsyncSession):
        self.sess:AsyncSession = sess

    async def insert_canvas(self, canvas: Canvas) -> bool:
            try:
                self.sess.add(canvas)
                await self.sess.flush() 
            except Exception as e:
                raise RuntimeError(f"Failed to insert a canvas: {e}")
            return True
    
    async def delete_canvas(self,manifest_id:str) -> bool:
        try:
           sql = delete(Canvas).where(Canvas.manifest_id == manifest_id)
           sql.execution_options(synchronize_session="fetch")
           await self.sess.execute(sql)
        except Exception as e :
            raise RuntimeError(f"Fail to delete a canvas:{e}")
        return True
    
    async def get_canvas_id(self,manifest_id:str) -> str:
        try:
            sql = select(Canvas.canvas_id).where(Canvas.manifest_id == manifest_id)
            sql.execution_options(synchronize_session="fetch")
            result = await self.sess.execute(sql)
            canvas_ids = result.scalars().all()
            return canvas_ids
        except Exception as e:
            raise RuntimeError(f"Failed to get a canvas_id: {e}")
        
    async def get_slug(self,canvas_id:str) -> dict:
        try:
            result = await self.sess.execute(
                select(Manifest._metadata)
                .join(Canvas, Manifest.manifest_id == Canvas.manifest_id)
                .where(Canvas.canvas_id == canvas_id)
            )
            _metadata = result.scalar_one_or_none()
            return _metadata
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve metadata: {e}")