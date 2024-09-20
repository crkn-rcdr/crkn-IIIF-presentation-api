import os
from dotenv import load_dotenv
import swiftclient
import logging


# load .env file
load_dotenv()
# Swift configuration
SWIFT_AUTH_URL = os.getenv("SWIFT_AUTH_URL")
SWIFT_USER = os.getenv("SWIFT_USER")
SWIFT_KEY = os.getenv("SWIFT_KEY")
CONTAINER_NAME = os.getenv("CONTAINER_NAME ")
 # load logger which defined in main.py
logger = logging.getLogger("Presentation_logger")

def get_swift_connection():
    return swiftclient.Connection(
        user=SWIFT_USER,
        key=SWIFT_KEY,
        authurl=SWIFT_AUTH_URL,
    )
