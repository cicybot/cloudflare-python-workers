import urllib.parse
import logging

import pyotp
from fastapi import APIRouter, Form

from common import helpers

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/utils",
    dependencies=[],
    tags=["Utils"],
    responses={404: {"description": "Not found"}},
)

@router.post("/otp")
async def generate_otp(token_index: str = Form(...)):
    """
    according TOKEN to gen opt
    """
    try:
        otps = helpers.get_otps()
        if not token_index or not token_index.strip():
            return {
                "status": "400",
                "errMsg":"token_index cannot be empty"
            }
        if otps.get(token_index,None) is None:
            return {
                "status": "400",
                "errMsg":"not found token"
            }
        totp = pyotp.TOTP(otps.get(token_index))
        otp_code = totp.now()

        return {
            "status": "200",
            "message": "OTP generated successfully",
            "otp": otp_code
        }

    except ValueError as e:
        logger.error(e)
        return {
            "status": "400",
            "errMsg":f"Invalid TOKEN format: {str(e)}"
        }

    except Exception as e:
        logger.error(e)
        return {
            "status": "500",
            "errMsg":f"Internal server error: {str(e)}"
        }


@router.get("/password/gen")
async def gen_password(password:str):
    pwd = helpers.get_password_hash(password)
    return {
        "password": pwd,
        "password_base64": urllib.parse.quote(pwd)
    }

@router.get("/password/verify")
async def gen_password(password:str,password_hash:str):
    return {
        "result": helpers.verify_password(password, password_hash)
    }