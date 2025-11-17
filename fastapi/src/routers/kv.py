import logging

from fastapi import Depends, APIRouter,Form
from fastapi.security import HTTPBearer
import json
from common import helpers
from service.CloudFlareClient import CloudFlareClient
import traceback

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/api/kv",
    dependencies=[],
    tags=["KV API"],
    responses={404: {"description": "Not found"}},
)

@router.post("/get")
async def kv_get(key: str = Form(...,examples=["test_key"])):
    try:
        if not key or not key.strip():
            return {
                "status": "400",
                "errMsg":"key cannot be empty"
            }
        res = await CloudFlareClient.get_instance().kv_get(key)
        return {
            "status": "200",
            "body":res
        }
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        return {
            "status": "500",
            "errMsg":"Internal server error"
        }

@router.post("/delete")
async def kv_delete(key: str = Form(...,examples=["test_key"])):
    try:
        if not key or not key.strip():
            return {
                "status": "400",
                "errMsg":"key cannot be empty"
            }
        res = await CloudFlareClient.get_instance().kv_delete(key)
        return {
            "status": "200",
            "body":res
        }
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        return {
            "status": "500",
            "errMsg":"Internal server error"
        }
@router.post("/put")
async def kv_put(key: str = Form(...,examples=["test_key"]),value: str = Form(...,examples=["test_value"])):
    try:
        if not key or not key.strip():
            return {
                "status": "400",
                "errMsg":"key cannot be empty"
            }
        if not value or not value.strip():
            return {
                "status": "400",
                "errMsg":"value cannot be empty"
            }
        res = await CloudFlareClient.get_instance().kv_put(key,value)
        return {
            "status": "200",
            "body":res
        }
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        return {
            "status": "500",
            "errMsg":"Internal server error"
        }
