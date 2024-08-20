import os
from dotenv import load_dotenv
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

# Load .env file
load_dotenv()

# Read environment variables
BACKEND_CORS_ORIGINS = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:8000").split(',')
OPENAPI_CLIENT_ID = os.getenv("OPENAPI_CLIENT_ID", "")
APP_CLIENT_ID = os.getenv("APP_CLIENT_ID", "")
TENANT_ID = os.getenv("TENANT_ID", "")
SCOPE_DESCRIPTION = os.getenv("SCOPE_DESCRIPTION", "user_impersonation")
ADMIN_URL_EXTERNAL = os.getenv("ADMIN_URL_EXTERNAL", "")
AUTH_URL = os.getenv("AUTH_URL", "")
AUTH_SECRET = os.getenv("AUTH_SECRET", "")
ADMIN_PORT = os.getenv("ADMIN_PORT", "")

# Build necessary values
SCOPE_NAME = f'api://{APP_CLIENT_ID}/{SCOPE_DESCRIPTION}'
SCOPES = {
    SCOPE_NAME: SCOPE_DESCRIPTION,
}
OPENAPI_AUTHORIZATION_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
OPENAPI_TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Initialize Azure AD authentication scheme
azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=APP_CLIENT_ID,
    tenant_id=TENANT_ID,
    scopes=SCOPES,
)
