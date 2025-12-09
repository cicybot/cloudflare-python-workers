import logging
from fastapi import APIRouter, Form
from common import crypto,utils
import os
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
        "info": crypto.aes_decrypt(pwd,response.text).split("\n"),
    }

@router.post("/encrypt")
async def encrypt(pwd: str = Form(...)):
    if Global.get_options("is_cf") is not None:
        return {}

    # if pwd.startswith("Pwd@") is False:
    #     return {
    #         "err":"password is not valid"
    #     }

    file_info_data = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__),"../../assets")),"info.data")
    file_info_data_plain = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__),"../../assets")),"info.data.log")
    if utils.file_exists(file_info_data_plain) is False:
        return {"err":"not found file"}
    data_info = utils.file_get_content(file_info_data_plain)
    utils.file_put_content(file_info_data,crypto.aes_encrypt(pwd,data_info))

    plain = crypto.aes_decrypt(pwd,utils.file_get_content(file_info_data))

    return {
        "plain":plain.split("\n"),
        'file':utils.file_get_content(file_info_data),
    }