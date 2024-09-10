from sqlalchemy.ext.asyncio import AsyncSession
from repository.manifest import  ManifestRepository
from repository.canvas import CanvasRepository
from repository.annotation_page import AnnotationPageRepository
from repository.annotation import AnnotationRepository
from models.data.presentation_models import Manifest,Canvas,AnnotationPage,Annotation
import logging
from swift_config.swift_config import get_swift_connection
import json
import os
from dotenv import load_dotenv


async def manifest_task(manifest_dict: dict, db: AsyncSession,iiif_url:str,slug:str):
    # load .env file
    load_dotenv()
    #container_name =  os.getenv("CONTAINER_NAME")
    # load logger which defined in main.py
    logger = logging.getLogger("Presentation_logger")
    # Connect to Swift
    #conn = get_swift_connection()

    manifest_id = "/".join(manifest_dict['id'].split('/')[-2:])
    #canvas_content = manifest_dict['items']
    #for data in conn.get_container(container_name)[1]:
      #print('{0}\t{1}\t{2}'.format(data['name'], data['bytes'], data['last_modified']))
    """
    #extract values to upload files to swift
    for canvas_item in canvas_content:
         
        canvas_id = "/".join(canvas_item['id'].split("/")[-2:])
        canvas_name = f'{slug}/{canvas_id}/canvas.json'
        canvas_content = canvas_item
        #upload canvas to swift
        conn.put_object(
                container_name,
                canvas_name,
                contents=json.dumps(canvas_content)
            )  
        annotation_page_content = canvas_item['items']
        annotation_page_id = "/".join(annotation_page_content[0]['id'].split("/")[-6:-4])
        annotation_page_suffix = "/".join(annotation_page_content[0]['id'].split("/")[-1:])
        annotation_page_name = f'{slug}/{canvas_id}/{annotation_page_id}/{annotation_page_suffix}/annotation_page.json'

        #upload annotation_page to swift
        conn.put_object(
                container_name,
                annotation_page_name,
                contents=json.dumps(annotation_page_content)
            )  
        
        #upload annotation to swift
        for annotation in annotation_page_content:
            #print(annotation)
            annotation_id = "/".join(annotation['items'][0]['id'].split("/")[-4:])
            #print(annotation_id)
            annotation_name = f'{slug}/{annotation_page_id}/{annotation_id}/annotation.json'
            annotation_content = annotation['items']
        
            conn.put_object(
                container_name,
                annotation_name,
                contents=json.dumps(annotation_content)
            )  
            
            
    logger.info("All files uploaded successfully.")
    print("uploaded all files") 
    """
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
        "value": {
            "none": [slug]
        }
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
            raise RuntimeError(f"Fail to read database:{e}")
        else:
            # Commit the transaction if all operations succeed
            await db.commit() 
            
    
    