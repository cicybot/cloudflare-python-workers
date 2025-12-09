import logging
from fastapi import APIRouter, Form
from common import crypto

import requests

from service.Global import Global

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/personal",
    dependencies=[],
    tags=["Personal"],
    responses={404: {"description": "Not found"}},
)

@router.post("/info")
async def info(pwd: str = Form(...),info_url: str = Form(None)):
    if info_url.startswith("https://") is False:
        info_url = Global.get_options("INFO_URL")
    response = requests.get(info_url)
    return {
        "info": crypto.aes_decrypt(pwd,response.text),
    }

@router.get("/encrypt")
async def info():
    if Global.get_options("is_cf") is not None:
        return {}

    return {
        # "info": crypto.aes_encrypt(pwd,response.text),
    }