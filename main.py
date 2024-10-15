from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Azure_auth.auth import BACKEND_CORS_ORIGINS, OPENAPI_CLIENT_ID, SCOPE_NAME
from api.manifest import router as manifest_router
from api.canvas import router as canvas_router
from fastapi.responses import RedirectResponse
from utils.lifespan_handler import lifespan
app = FastAPI(
    swagger_ui_oauth2_redirect_url='/oauth2-redirect',
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': OPENAPI_CLIENT_ID,
        'scopes': SCOPE_NAME,
    },
    title="IIIF Presentation API",
    description="Presentation API is to provide the information necessary to allow a rich, online viewing environment for compound digital objects to be presented to a human user, often in conjunction with the IIIF Image API",
    summary="This is the sole purpose of the API and therefore descriptive information is given in a way that is intended for humans to read, but not semantically available to machines.",
    version="0.0.1",
    terms_of_service="https://www.crkn-rcdr.ca/en/tools-and-services",
    contact={
        "name": "CRKN",
        "url": "https://www.crkn-rcdr.ca/en/about-crkn",
        "email": "mzheng@crkn.ca",
    },
    license_info={
        "name": "Licensing",
        "url": "https://www.crkn-rcdr.ca/en/crkn-licensing-principles",
    },
    lifespan=lifespan
)
origins = [
   '*'
]
if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
@app.get("/",include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")
   
app.include_router(manifest_router)
app.include_router(canvas_router)


