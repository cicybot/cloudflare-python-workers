import logging

import pyotp
from fastapi import APIRouter, Form

from common import helpers
from service.Global import Global

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/utils",
    dependencies=[],
    tags=["Utils"],
    responses={404: {"description": "Not found"}},
)

@router.post("/otp")
async def generate_otp(index: int = Form(...)):
    """
    according TOKEN to gen opt
    """
    try:
        logger.info(index)
        otps = helpers.get_otps()
        keys = [ v for v in otps.values()]
        totp = pyotp.TOTP(keys[index])
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
    return {
        "password": helpers.get_password_hash(password)
    }

@router.get("/password/verify")
async def gen_password(password:str,password_hash:str):
    return {
        "result": helpers.verify_password(password, password_hash)
    }
