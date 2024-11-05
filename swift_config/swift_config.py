import os
from dotenv import load_dotenv
import swiftclient
import logging
from swiftclient.exceptions import ClientException
from fastapi import HTTPException

# load .env file
load_dotenv()
# Swift configuration
SWIFT_AUTH_URL = os.getenv("SWIFT_AUTH_URL")
SWIFT_USER = os.getenv("SWIFT_USER")
SWIFT_KEY = os.getenv("SWIFT_KEY")
SWIFT_PREAUTH_URL = os.getenv("SWIFT_PREAUTH_URL")
CONTAINER_NAME = os.getenv("CONTAINER_NAME ")

#config logger
logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

def get_swift_connection():
    try:
        
        return swiftclient.Connection(
            user=SWIFT_USER,
            key=SWIFT_KEY,
            authurl=SWIFT_AUTH_URL,
            preauthurl=SWIFT_PREAUTH_URL
    )
    
    except (ClientException) as conn_error:
        logger.error(f"Failed to connect to Swift: {conn_error}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Swift: {conn_error}")
