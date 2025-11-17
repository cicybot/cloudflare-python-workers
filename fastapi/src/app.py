import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware

from common import helpers, constants
from service.Global import Global
from routers import auth, d1, utils,kv

os.environ['TZ'] = 'UTC'

log_level = logging.INFO if Global.is_local() is False else logging.DEBUG

log_dir = os.getenv("LOG_DIR",None)
log_handlers = [
    logging.StreamHandler()
]
if log_dir is not None:
    log_file = f"{log_dir}/app.log"
    log_handlers = [
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]

logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s][%(name)s/%(funcName)s:%(lineno)d] %(message)s',
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Global.init()
    yield


app = FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    **constants.CORS_OPTIONS,
)
app.include_router(auth.router)
app.include_router(d1.router)
app.include_router(utils.router)
app.include_router(kv.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/swagger")

@app.get("/swagger",response_class=HTMLResponse, include_in_schema=False)
async def swagger(credentials:HTTPBasicCredentials = Depends(helpers.http_basic_security)):
    return  constants.SWAGGER_HTML
