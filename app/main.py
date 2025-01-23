from logging import getLogger
from fastapi import FastAPI

from app.api.api import api_router
from app.core.config import ConfigManager
from app.core.logger import load_looger


config = ConfigManager().config

load_looger()
logger = getLogger('ocr')
logger.info('Start Ocreniisan.')

app = FastAPI(
    root_path='/ocreniisan',
    docs_url='/docs',
    openapi_url='/openapi.json',
)

app.include_router(api_router)
