from fastapi import HTTPException
async def get_slug(repo,id):
     try:
        _metadata = await repo.get_slug(id)
        if _metadata is None  or "value" not in _metadata[0] or "none" not in _metadata[0]["value"]:
            raise HTTPException(status_code=404, detail=f"Slug not found for the associated ID: {id}")
        slug =  _metadata[0]["value"]["none"][0]
        return slug
     except Exception as e:
        raise HTTPException(status_code=404, detail=f"Slug not found for the associated ID: {id}")