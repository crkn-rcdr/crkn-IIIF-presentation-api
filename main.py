from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Azure_auth.auth import azure_scheme,BACKEND_CORS_ORIGINS, OPENAPI_CLIENT_ID, SCOPE_NAME
from api.manifest import router as manifest_router
from api.canvas import router as canvas_router
from api.annotation_page import router as annotation_page_router
from api.annotation import router as annotation_router
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
#config logger
logging.basicConfig(level=logging.ERROR,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Presentation_logger")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()
    yield
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

)
if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    
app.include_router(manifest_router)
app.include_router(canvas_router)
app.include_router(annotation_page_router)
app.include_router(annotation_router)
