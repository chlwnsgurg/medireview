"""
APScheduler 기반 주기적 리뷰 수집 스케줄러
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from database import SessionLocal
from services.crawler import sync_all_reviews

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _sync_job():
    """스케줄러에서 실행되는 리뷰 동기화 작업"""
    logger.info("스케줄러: 리뷰 동기화 작업 시작")
    db = SessionLocal()
    try:
        count = sync_all_reviews(db)
        logger.info(f"스케줄러: 리뷰 동기화 완료 — 신규 {count}건")
    except Exception as e:
        logger.error(f"스케줄러: 리뷰 동기화 실패 — {e}")
    finally:
        db.close()


def start_scheduler():
    """스케줄러 시작 (FastAPI lifespan에서 호출)"""
    interval = settings.SYNC_INTERVAL_MINUTES
    scheduler.add_job(
        _sync_job,
        "interval",
        minutes=interval,
        id="sync_reviews",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"스케줄러 시작: {interval}분 간격으로 리뷰 동기화")


def stop_scheduler():
    """스케줄러 종료"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료")
