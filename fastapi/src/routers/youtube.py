import logging
import os

from fastapi import APIRouter,HTTPException
import requests
from google_auth_oauthlib.flow import InstalledAppFlow



logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/youtbe",
    dependencies=[],
    tags=["Youtube"],
    responses={404: {"description": "Not found"}},
)

@router.get("/snippets")
async def snippets(videoId:str):
    url = "https://www.googleapis.com/youtube/v3/captions"
    params = {
        "part": "snippet",
        "videoId": videoId if videoId is not None else "qp0HIF3SfI4",
        "key": os.getenv("YT_API_KEY_SHADOWING_PRACTICE")
    }

    response = requests.get(url, params=params)
    data = response.json()
    items = data.get("items", [])

    # keep en* and zh* only
    filtered = []
    for item in items:
        snip = item.get("snippet", {})
        lang = snip.get("language", "")

        if lang.startswith("en") or lang.startswith("zh-CN"):
            filtered.append(
                {
                    "caption_id": item.get("id"),
                    "language": lang,
                    "name": snip.get("name"),
                    "is_auto_generated": snip.get("trackKind") == "ASR",
                }
            )

    return {
        "count": len(filtered),
        "captions": filtered,
    }


@router.get("/caption")
async def caption(captionId: str):

    """
    Download subtitle (vtt) by captionId
    """
    access_token = os.getenv("GOOGLE_ACCESS_TOKEN")

    url = f"https://www.googleapis.com/youtube/v3/captions/{captionId}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    params = {
        "tfmt": "vtt"      # vtt format; could also use 'srt'
    }

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    subtitle_text = resp.json()

    return {
        "access_token":access_token,
        "captionId": captionId,
        "format": "vtt",
        "subtitle": subtitle_text
    }

