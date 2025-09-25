import aiohttp
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
# import redis.asyncio as aioredis -- TODO: add back when on production servers
from fastapi import HTTPException
from swift_config.swift_config import get_swift_connection
from utils.settings import swift_user, swift_key, swift_auth_url, redis_url
from Azure_auth.auth import azure_scheme
import asyncio


# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for storing authentication token and storage URL
swift_token = None
swift_storage_url = None
swift_session = None 

@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan events including startup and shutdown tasks.
    """
    global swift_token, swift_storage_url, swift_session
    swift_session = aiohttp.ClientSession()
    
    try:
        # Load OPENID config
        await initialize_openid_config()
        
        # Swift authentication
        swift_token, swift_storage_url = await initialize_swift()
        
        # Store swift_session, swift_token, and swift_storage_url in app state for later use
        app.state.swift_session = swift_session
        app.state.swift_token = swift_token
        app.state.swift_storage_url = swift_storage_url
        
        # Initialize Redis connection
        # app.state.redis = aioredis.from_url(
        #     redis_url,
        #     decode_responses=False  
        # )
  
        """
        conn = get_swift_connection()
        app.state.conn = conn
        """
        # Start the token refresh task and pass the app to it
        app.state.token_refresh_task = asyncio.create_task(refresh_token_periodically(app))

        yield
    except Exception as e:
        logger.error(f"Error during lifespan setup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect storage or Redis servers")
    
    finally:
        # Cancel the token refresh task
        app.state.token_refresh_task.cancel()
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

async def initialize_swift():
    global swift_session, swift_storage_url, swift_token

    # Perform Swift authentication 
    headers = {
        "X-Auth-User": swift_user,
        "X-Auth-Key": swift_key
    }
    try:
        async with swift_session.get(swift_auth_url, headers=headers) as resp:
            if resp.status in (200, 204):
                swift_token = resp.headers.get("X-Auth-Token")
                swift_storage_url = resp.headers.get("X-Storage-Url")
                if not swift_token or not swift_storage_url:
                    raise Exception("Authentication failed: missing token or storage URL.")
                return swift_token, swift_storage_url
            else:
                error_message = await resp.text()
                logger.error(f"Authentication failed: {error_message}")
                raise Exception(f"Authentication failed: Status code {resp.status}, response content: {error_message}")
    except Exception as e:
        logger.error(f"Failed during Swift initialization: {e}")
        raise

async def refresh_token_periodically(app):
    """ 
    Refresh the Swift token every 2 hours and update app state.
    """
    global swift_token, swift_storage_url
    while True:
        try:
            logger.info("Refreshing Swift token...")
            swift_token, swift_storage_url = await initialize_swift()
            logger.info("Swift token refreshed successfully.")

            # Update app.state with the new token and storage URL
            app.state.swift_token = swift_token
            app.state.swift_storage_url = swift_storage_url
        except Exception as e:
            logger.error(f"Error refreshing Swift token: {e}")
        
        # Wait for 2 hours before refreshing again
        await asyncio.sleep(2 * 60 * 60)
        
async def close_session(app):
    """
    Close the aiohttp session and Redis connection when the application shuts down.
    """
    global swift_session
    # Cancel the token refresh task
    try:
        if hasattr(app.state, 'token_refresh_task'):
            app.state.token_refresh_task.cancel()
            await app.state.token_refresh_task
            logger.info("Cancelled the token refresh task.")
    except Exception as e:
        logger.error(f"Error cancelling the token refresh task: {e}")

    # Close the aiohttp session
    try:
        if swift_session:
            await swift_session.close()
            logger.info("Closed aiohttp session.")
    except Exception as e:
        logger.error(f"Error closing aiohttp session: {e}")
    
    # Close the Redis connection
    try:
        if hasattr(app.state, 'redis') and app.state.redis:
            await app.state.redis.close()
            logger.info("Closed Redis connection.")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")
