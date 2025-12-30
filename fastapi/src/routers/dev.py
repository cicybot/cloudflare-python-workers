import logging
from fastapi import APIRouter
import requests

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
async def dev():
    if Global.get_options("is_cf") is not None:
        return {}





    url = "https://www.googleapis.com/youtube/v3/captions"

    params = {
        "part": "snippet",
        "videoId": "qp0HIF3SfI4",
        "key": "AIzaSyAQawQW1JIT4Wqagw0eDcJLgemlr3TEco0"
    }

    response = requests.get(url, params=params)
    data = response.json()

    print(data)
    return {
        "data":data,
    }

