import aiohttp
import aioboto3
import botocore
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dotenv import load_dotenv
from Azure_auth.auth import azure_scheme
import os
import redis.asyncio as aioredis
from fastapi import HTTPException

#config logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()
swift_user = os.getenv("SWIFT_USER")
swift_key = os.getenv("SWIFT_KEY")
swift_auth_url = os.getenv("SWIFT_AUTH_URL")
container_name = os.getenv("CONTAINER_NAME")
redis_url = os.getenv("REDIS_URL")

#Global variables for storing authentication token and storage URL
swift_token = None
swift_storage_url = None
swift_session = None 

@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None,None]:
    """
    Manage application lifespan events including startup and shutdown tasks.
    """
    global swift_token,swift_storage_url,swift_session
    swift_session = aiohttp.ClientSession()
    
    try:
        #load OPENID config
        await initialize_openid_config()
        """
        #swift authentication
        swift_token, swift_storage_url = await initialize_swift()
        # Store swift_session, swift_token, and swift_storage_url in app state for later use
        app.state.swift_session = swift_session
        app.state.swift_token = swift_token
        app.state.swift_storage_url = swift_storage_url
        """
        # Initialize Redis connection
        app.state.redis = aioredis.from_url(
            redis_url,
            decode_responses=False  
            
        )
       
        yield
    except Exception as e:
        logger.error(f"Error during lifespan setup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect storage or redis servers")
    
    finally:
        await close_session(app)
       

async def initialize_openid_config():
    """
    Load OpenID configuration on startup.
    """
    try:
        await azure_scheme.openid_config.load_config()
    except Exception as e:
        logger.error(f"Failed to load OpenID configuration: {e}")
        raise

async def  initialize_swift():
    global swift_session,swift_storage_url,swift_token

    #Perform Swift authentication and initialize required containers.

    headers = {
        "X-Auth-User":swift_user,
        "X-Auth-Key":swift_key
    }
    try:
        async with swift_session.get(swift_auth_url,headers=headers) as resp:
            if resp.status in(200,204):
                swift_token = resp.headers.get("X-Auth-Token")
                swift_storage_url = resp.headers.get("X-Storage-Url")
                if not swift_token or not swift_storage_url:
                    raise Exception("Authentication failed:missing token or storage URL.")
                return swift_token, swift_storage_url
            else:
                error_message = await resp.text()
                logger.error(f"Authentication failed: {error_message}")
                raise Exception(f"Authentication failed: Status code {resp.status}, response content: {error_message}")
    except Exception as e:
        logger.error(f"Failed during Swift initialization: {e}")
        raise



async def close_session(app):
    """
    Close the aiohttp session and Redis connection when the application shuts down.
    
    global swift_session
    try:
        if swift_session:
            await swift_session.close()
            logger.info("Closed aiohttp session.")
    except Exception as e:
        logger.error(f"Error closing aiohttp session: {e}")
    """
    try:
        if hasattr(app.state, 'redis') and app.state.redis:
            await app.state.redis.close()
            logger.info("Closed Redis connection.")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")

   