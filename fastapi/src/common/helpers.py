from datetime import datetime, timedelta, timezone
from typing import Union
import logging
import jwt
from fastapi import Depends, HTTPException, status,Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer,HTTPAuthorizationCredentials
from pwdlib import PasswordHash

from common.constants import auth_strip_path_prefixes
from service.Global import Global
from service.CloudFlareClient import CloudFlareClient
logger = logging.getLogger(__name__)

http_basic_security = HTTPBasic()
http_bearer_security = HTTPBearer(auto_error=False)

password_hash = PasswordHash.recommended()

def verify_http_basic_credentials(credentials: HTTPBasicCredentials = Depends(http_basic_security)):
    if credentials.username != Global.get_options("SWAGGER_USERNAME") or credentials.password != Global.get_options("SWAGGER_PASSWORD"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    logger.info(datetime.utcnow().timestamp())

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Global.get_options("JWT_SECRET_KEY"), algorithm=Global.get_options("JWT_ALGORITHM"))
    return encoded_jwt,expire

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

async def get_current_user_uid(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer_security)):

    url_path = request.url.path

    if any(url_path.startswith(prefix) for prefix in auth_strip_path_prefixes):
        request.state.uid = None
        return None
    else:
        if not credentials:
            raise HTTPException(status_code=401, detail="Authorization header required")

        token = credentials.credentials

        try:
            payload = jwt.decode(token, Global.get_options("JWT_SECRET_KEY"), algorithms=[Global.get_options("JWT_ALGORITHM")])
            request.state.uid = payload.get("uid")
            return payload.get("uid")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_cf_client() -> CloudFlareClient:
    return CloudFlareClient.get_instance()


def get_otps():
    options = Global.get_options()
    otps = {}
    for key in options.keys():
        if key[:4] == 'OTP_':
            otps[key[4:]] = options[key]
    return otps