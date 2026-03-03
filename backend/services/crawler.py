"""
리뷰 수집 통합 서비스
각 플랫폼 크롤러를 호출하고 DB에 저장합니다.
"""
import json
import logging

from sqlalchemy.orm import Session

from models import Hospital, Review
from services.naver_crawler import fetch_naver_reviews
from services.alert_service import check_and_create_alert

logger = logging.getLogger(__name__)


def _save_reviews(db: Session, hospital_id: int, raw_reviews: list[dict]) -> int:
    """
    크롤링된 리뷰를 DB에 저장합니다. (중복 제외)
    저평점 리뷰는 알림을 자동 생성합니다.
    Returns: 신규 저장된 리뷰 수
    """
    saved = 0
    for r in raw_reviews:
        # 중복 체크
        existing = (
            db.query(Review)
            .filter(
                Review.hospital_id == hospital_id,
                Review.platform_review_id == r["platform_review_id"],
            )
            .first()
        )
        if existing:
            continue

        review = Review(
            hospital_id=hospital_id,
            platform=r["platform"],
            platform_review_id=r["platform_review_id"],
            author=r.get("author", "익명"),
            rating=r["rating"],
            rating_scale=r.get("rating_scale", 5),
            content=r.get("content", ""),
            image_urls=json.dumps(r.get("image_urls", []), ensure_ascii=False),
            reviewed_at=r.get("reviewed_at"),
        )
        db.add(review)
        db.flush()  # ID 할당을 위해 flush

        # 저평점 알림 체크
        check_and_create_alert(db, review)

        saved += 1

    if saved > 0:
        db.commit()

    return saved


def sync_naver_reviews(db: Session) -> int:
    """네이버 지도 리뷰 동기화"""
    hospital = db.query(Hospital).first()
    if not hospital or not hospital.naver_place_id:
        logger.warning("병원 정보 또는 네이버 Place ID가 없습니다.")
        return 0

    logger.info(f"네이버 리뷰 동기화 시작: place_id={hospital.naver_place_id}")
    raw_reviews = fetch_naver_reviews(hospital.naver_place_id)
    saved = _save_reviews(db, hospital.id, raw_reviews)
    logger.info(f"네이버 리뷰 동기화 완료: 신규 {saved}건")
    return saved


def sync_all_reviews(db: Session) -> int:
    """모든 플랫폼에서 리뷰 동기화 (MVP: 네이버만)"""
    total = 0
    total += sync_naver_reviews(db)
    # v2: total += sync_modudoc_reviews(db)
    # v2: total += sync_goodoc_reviews(db)
    return total
