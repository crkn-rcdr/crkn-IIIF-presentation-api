import os
from dotenv import load_dotenv
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from fastapi import Depends,HTTPException
import jwt
# load .env file
load_dotenv()
jwt_secret = os.getenv("EDITOR_SECRET_KEY")

#define a HTTPBearer to handle the token from client
client_token_scheme = HTTPBearer()
# JWT authentication function
def jwt_auth(auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    if not auth:
        # Raise an exception if no authorization header is provided
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        # Decode the JWT token using the secret
        payload = jwt.decode(auth.credentials, jwt_secret, algorithms=["HS256"])
        # If decoding is successful, return the payload
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")