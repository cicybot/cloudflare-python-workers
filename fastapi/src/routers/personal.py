import logging
from fastapi import APIRouter, Form, Response
from common import crypto,utils,helpers
import os
import requests
import urllib.parse

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
    if info_url is None or info_url == "":
        return {
            "status": "500",
            "errMsg":"info_url cannot be empty"
        }

    response = requests.get(info_url)

    # Check if the request was successful
    if response.status_code != 200:
        return {
            "status": "500",
            "errMsg":"url cannot access"
        }
    else:
        try:
            decrypted_content = crypto.aes_decrypt(pwd,response.text.strip())
            return Response(content=decrypted_content, media_type="text/plain")
        except:
            return {
                "status": "500",
                "errMsg":"decrypt error"
            }

@router.post("/encrypt")
async def encrypt(pwd: str = Form(...)):
    if Global.get_options("is_cf") is not None:
        return {}
    pwd_hash = urllib.parse.unquote(Global.get_options("PWD_PERSONAL"))

    if helpers.verify_password(pwd, pwd_hash) is False:
        return {
            "err":"password is not valid"
        }

    file_info_data_plain = os.path.abspath("/Users/data/personal.md")

    if utils.file_exists(file_info_data_plain) is False:
        return {"err":"not found file"}
    data_info = utils.file_get_content(file_info_data_plain)

    return Response(content=crypto.aes_encrypt(pwd,data_info), media_type="text/plain")
