"""
APScheduler 기반 주기적 리뷰 수집 스케줄러
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from database import SessionLocal
from services.crawler import sync_all_reviews
from services.automation_service import batch_auto_reply

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _sync_job():
    """스케줄러에서 실행되는 리뷰 동기화 작업"""
    logger.info("스케줄러: 리뷰 동기화 작업 시작")
    db = SessionLocal()
    try:
        count = sync_all_reviews(db)
        logger.info(f"스케줄러: 리뷰 동기화 완료 — 신규 {count}건")

        # 동기화 후 미답변 리뷰 자동 대응 처리 (실패 재시도 포함)
        try:
            result = batch_auto_reply(db)
            logger.info(f"스케줄러: 자동 대응 완료 — {result}")
        except Exception as e:
            logger.error(f"스케줄러: 자동 대응 실패 — {e}")
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
