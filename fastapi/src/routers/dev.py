import logging

import pyotp
from fastapi import APIRouter, Form

from common import helpers
from service.Global import Global

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/dev",
    dependencies=[],
    tags=["Dev"],
    responses={404: {"description": "Not found"}},
)

@router.get("/options")
async def options():
    if Global.get_options("is_cf") is not None:
        return {}
    return Global.get_options()


@router.get("/")
async def options():
    if Global.get_options("is_cf") is not None:
        return {}
    return Global.get_options()

