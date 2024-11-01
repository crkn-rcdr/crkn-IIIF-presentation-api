from sqlalchemy.ext.asyncio import AsyncSession
from repository.manifest import  ManifestRepository
from repository.canvas import CanvasRepository
from repository.annotation_page import AnnotationPageRepository
from repository.annotation import AnnotationRepository
from models.data.presentation_models import Manifest,Canvas,AnnotationPage,Annotation
import logging
from fastapi import HTTPException

async def manifest_task(manifest_dict: dict, db: AsyncSession,iiif_url:str,slug_value_dict:dict):
    #config logger
    logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
    logger = logging.getLogger(__name__)
    manifest_id = "/".join(manifest_dict['id'].split('/')[-2:])
    #extract values from manifest_dict to tables
    context = manifest_dict.get("@context",['https://iiif.io/api/presentation/3/context.json'])
    context = [context] if isinstance(context, str) else context
    manifest_table = Manifest(
        context=context,
        id=manifest_dict.get('id',iiif_url + 'manifest/' + manifest_id),
        manifest_id=manifest_id,
        type=manifest_dict.get('type','Manifest'),
        label=manifest_dict.get('label'),
        _metadata=manifest_dict.get('metadata',{
        "label": {
            "none": ["slug"]
        },
        "value": slug_value_dict
    }),
        provider=manifest_dict.get('provider',[{
            'id': 'https://www.crkn-rcdr.ca/',
            'type': 'Agent',
            'label': {
                'en': ['Canadian Research Knowledge Network'],
                'fr': ['Réseau canadien de documentation pour la recherche']
            },
            'homepage': [{
                'id': 'https://www.crkn-rcdr.ca/',
                'type': 'Text',
                'label': {
                    'en': ['Canadian Research Knowledge Network'],
                    'fr': ['Réseau canadien de documentation pour la recherche']
                },
                'format': 'text/html'
            }]
        }]),
        summary=manifest_dict.get('summary'),
        requiredStatement=manifest_dict.get('requiredStatement'),
        rights=manifest_dict.get('rights'),
        thumbnail=manifest_dict.get('thumbnail'),
        viewingDirection=manifest_dict.get('viewingDirection'),
        behavior=manifest_dict.get('behavior'),
        seeAlso=manifest_dict.get('seeAlso'),
        start=manifest_dict.get('start'),
        structures=manifest_dict.get('structures'),
        annotations=manifest_dict.get('annotations'),
        navPlace=manifest_dict.get('navPlace'),
        rendering=manifest_dict.get('rendering'),
        homepage=manifest_dict.get('homepage')
        
    )
    manifest_repo = ManifestRepository(db)
    canvas_repo = CanvasRepository(db)
    annotation_page_repo = AnnotationPageRepository(db)
    annotation_repo = AnnotationRepository(db)
    async with db.begin():
        try:
            check_manifest_id = await manifest_repo.get_manifest_id(manifest_id)
             # if manifest_id exists, delete it and all records associate with it
            if check_manifest_id:
                    canvas_ids = await canvas_repo.get_canvas_id(manifest_id)
                    for canvas_id in canvas_ids:
                        annotation_page_id = await annotation_page_repo.get_annotation_page_id(canvas_id)
                        await annotation_repo.delete_annotation(annotation_page_id)
                        await annotation_page_repo.delete_annotation_page(canvas_id)
                    await canvas_repo.delete_canvas(manifest_id)
                    await manifest_repo.delete_manifest(manifest_id)
            await manifest_repo.insert_manifest(manifest_table)
        
            for canvas in manifest_dict['items']:
                canvas_id = "/".join(canvas['id'].split('/')[-2:])
                canvas_table = Canvas(
                   manifest_id=manifest_id,
                   canvas_id=canvas_id,
                   id=canvas.get('id',iiif_url + 'canvas/' + canvas_id),  
                   type=canvas.get('type','Canvas'),
                   label=canvas.get('label'),
                   height=canvas.get('height'),
                   width=canvas.get('width'),
                   thumbnail=canvas.get('thumbnail'),
                   items=canvas.get('items'),    
                   navPlace=canvas.get('navPlace'),
                   behavior=canvas.get('behavior'),
                   _metadata=canvas.get('metadata'),
                   requiredStatement=canvas.get('requiredStatement'),
                   seeAlso=canvas.get('seeAlso'),
                   rendering=canvas.get('rendering')
                )
                
                annotation_page_table = AnnotationPage(
                        id=canvas['items'][0]['id'],  
                        type=canvas['items'][0].get('type', 'AnnotationPage'),  
                        canvas_id=canvas_id,
                        context= ['http://iiif.io/api/presentation/3/context.json']
                    )
                await canvas_repo.insert_canvas(canvas_table)
                annotation_page_id = await annotation_page_repo.insert_annotation_page(annotation_page_table)
                for annotation_item in canvas['items'][0]['items']:
                     annotation_table = Annotation(
                        annotation_page_id = annotation_page_id,
                        id = annotation_item['id'],
                        body = annotation_item['body'],
                        type = annotation_item.get('type','Annotation'),
                        target = annotation_item.get('target'),
                        motivation = annotation_item.get('motivation')
                     )
                     await annotation_repo.insert_annotation(annotation_table)
        except Exception as e:
            # Rollback the transaction in case of an error
            await db.rollback()  
            logger.error(f"Transaction failed and was rolled back: {str(e)}", exc_info=True)
            raise  HTTPException(status_code=500, detail="Fail to write data to database.")
        else:
            # Commit the transaction if all operations succeed
            await db.commit() 
            
    
    