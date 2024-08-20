from sqlalchemy.orm import Session
from models.data.presentation_models import Manifest
from sqlalchemy import update,delete,insert
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

class ManifestRepository:
    def __init__(self,sess:AsyncSession):
        self.sess:AsyncSession = sess

    async def insert_manifest(self, manifest: Manifest) -> bool:
        try:
            self.sess.add(manifest)
            await self.sess.flush()  
        except Exception as e:
            raise RuntimeError(f"Failed to insert a manifest: {e}")
        return True
    async def delete_manifest(self,manifest_id:str) -> bool:
        try:
           sql = delete(Manifest).where(Manifest.manifest_id == manifest_id)
           sql.execution_options(synchronize_session="fetch")
           await self.sess.execute(sql)
        except Exception as e:
            raise RuntimeError(f"Failed to delete a manifest: {e}")
        return True
    
    async def get_manifest_id(self,manifest_id:str) -> str:
        try:
            sql = select(Manifest.manifest_id).where(Manifest.manifest_id == manifest_id)
            sql.execution_options(synchronize_session="fetch")
            result = await self.sess.execute(sql)
            manifest_id = result.scalar_one_or_none()
        except Exception as e:
            raise RuntimeError((f"Failed to get a manifest: {e}"))
        return manifest_id
    
    async def get_slug(self,manifest_id:str) -> str:
        try:
            sql = select(Manifest._metadata).where(Manifest.manifest_id == manifest_id)
            sql.execution_options(synchronize_session="fetch")
            result = await self.sess.execute(sql)
            _metadata = result.scalar_one_or_none()
        except Exception as e:
            raise RuntimeError(f"Failed to get a metadata:{e}")
        return _metadata
        