import logging
from datetime import timedelta
from typing import Optional

from fastapi import Depends, APIRouter,Request
from fastapi.security import HTTPBearer

from common import helpers
from service.Global import Global

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/api/auth",
    dependencies=[Depends(helpers.get_current_user_uid)],
    tags=["Auth"],
    responses={404: {"description": "Not found"}},
)

@router.get("/login")
async def login():
    access_token_expires = timedelta(minutes=Global.get_options("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
    logger.info("access_token_expires:%s",access_token_expires)

    access_token,expire = helpers.create_access_token(
        data={"uid": 1}, expires_delta=access_token_expires
    )
    return {
        "access_token":access_token,
        "expire":expire,
        "access_token_expires":access_token_expires,
    }


@router.get("/me")
async def me(request:Request, uid = Depends(helpers.get_current_user_uid)):
    return {
        "uid":uid,
        "uid1":request.state.uid,
    }