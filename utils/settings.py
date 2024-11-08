from dotenv import load_dotenv
import os

#Load .env file
load_dotenv()

#define environment variables
swift_user = os.getenv("SWIFT_USER")
swift_key = os.getenv("SWIFT_KEY")
swift_auth_url = os.getenv("SWIFT_AUTH_URL")
swift_preauth_url = os.getenv("SWIFT_PREAUTH_URL")
container_name = os.getenv("CONTAINER_NAME")
redis_url = os.getenv("REDIS_URL")
