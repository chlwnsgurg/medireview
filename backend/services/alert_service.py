"""
저평점 리뷰 알림 서비스
"""
import logging

from sqlalchemy.orm import Session

from models import Alert, Hospital, Review

logger = logging.getLogger(__name__)


def check_and_create_alert(db: Session, hospital: Hospital, review: Review) -> bool:
    """
    리뷰가 저평점 기준 이하이면 Alert를 생성합니다.

    Returns:
        알림이 생성되었으면 True
    """
    # 별점 정규화 (10점 만점이면 5점 기준으로 변환)
    normalized_rating = review.rating
    if review.rating_scale == 10:
        normalized_rating = review.rating / 2

    if normalized_rating > hospital.alert_threshold:
        return False

    # 중복 알림 체크
    existing = (
        db.query(Alert)
        .filter(Alert.review_id == review.id)
        .first()
    )
    if existing:
        return False

    alert = Alert(
        hospital_id=hospital.id,
        review_id=review.id,
        type="low_rating",
    )
    db.add(alert)
    db.commit()

    logger.info(
        f"저평점 알림 생성: review_id={review.id}, "
        f"rating={review.rating}/{review.rating_scale}, "
        f"threshold={hospital.alert_threshold}"
    )
    return True
