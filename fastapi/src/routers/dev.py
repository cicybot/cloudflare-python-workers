import logging
import urllib.parse

import pyotp
from fastapi import APIRouter

from common import helpers
from common import crypto
from service.Global import Global
def pad(s):
    return s + (16 - len(s) % 16) * chr(16 - len(s) % 16)

def unpad(s):
    return s[:-ord(s[-1])]

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/dev",
    dependencies=[],
    tags=["Dev"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def options():
    if Global.get_options("is_cf") is not None:
        return {}
    password = "password"   # You can replace this with any password
    text_to_encrypt = "Hello, this is a secret message!"

    encrypted_text = crypto.aes_encrypt(password, text_to_encrypt)
    decrypted_text = crypto.aes_decrypt(password, encrypted_text)

    return {
        "PWD_PERSONAL":urllib.parse.unquote(Global.get_options("PWD_PERSONAL")),
        "decrypted_text":decrypted_text,
        "encrypted_text":encrypted_text,
        "opts":helpers.get_otps(),
        "options":Global.get_options()
    }

