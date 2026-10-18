"""
시스템 설정 API 라우터
Chrome headless 모드 등 런타임 설정 조회/변경
"""
import logging

from fastapi import APIRouter

from config import settings
from schemas import ChromeHeadlessSetting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/chrome-headless", response_model=ChromeHeadlessSetting)
def get_chrome_headless():
    """Chrome headless 모드 조회"""
    return {"enabled": settings.CHROME_HEADLESS}


@router.put("/chrome-headless", response_model=ChromeHeadlessSetting)
def update_chrome_headless(body: ChromeHeadlessSetting):
    """Chrome headless 모드 변경 (메모리에만 반영, 서버 재시작 시 .env 값으로 복귀)"""
    settings.CHROME_HEADLESS = body.enabled
    logger.info(f"Chrome headless 모드 변경: {body.enabled}")
    return {"enabled": settings.CHROME_HEADLESS}
