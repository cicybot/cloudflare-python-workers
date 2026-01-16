import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session

from common.db import execute_sql, get_session
from service.Global import Global

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/utils",
    dependencies=[],
    tags=["Utils"],
    responses={404: {"description": "Not found"}},
)


@router.get("/options")
async def options():
    if Global.get_options("is_cf") is not None:
        return {}
    return Global.get_options()

@router.get("/test")
async def options(session: Session = Depends(get_session)):
    execute_sql("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password Text
);
    """, session=session)

    execute_sql("""
INSERT INTO users (username, password)
SELECT * FROM (
    VALUES
    ("tom", "password1"),
    ("jack", "password1")
) WHERE NOT EXISTS (SELECT 1 FROM users);
    """, session=session)


    execute_sql("""
INSERT INTO users (username, password)VALUES("jack", "password1")
    """, session=session)

    execute_sql("""
select * from users
    """, session=session)
    execute_sql("""
update users set username = "user1" where id = 1
    """, session=session)



    return {"status": "ok"}
