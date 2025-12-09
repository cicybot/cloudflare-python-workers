import logging
from fastapi import APIRouter

from common import helpers
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
    return {
        "opts":helpers.get_otps(),
        "options":Global.get_options()
    }

