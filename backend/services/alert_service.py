"""
알림 서비스
저평점 리뷰 감지 시 알림을 생성합니다.
"""
import logging

from sqlalchemy.orm import Session

from models import Alert, Hospital, Review

logger = logging.getLogger(__name__)


def check_and_create_alert(db: Session, review: Review) -> Alert | None:
    """
    리뷰 별점이 병원 설정 임계값 이하이면 알림 생성

    Args:
        db: DB 세션
        review: 저장된 리뷰 객체

    Returns:
        생성된 Alert 또는 None
    """
    hospital = db.query(Hospital).filter(Hospital.id == review.hospital_id).first()
    if not hospital:
        return None

    threshold = hospital.alert_threshold or 2

    if review.rating <= threshold:
        # 중복 알림 체크
        existing = (
            db.query(Alert)
            .filter(Alert.review_id == review.id)
            .first()
        )
        if existing:
            return None

        alert = Alert(
            hospital_id=hospital.id,
            review_id=review.id,
            type="low_rating",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        logger.info(
            f"저평점 알림 생성: 리뷰#{review.id} (별점 {review.rating}점, 임계값 {threshold}점)"
        )
        return alert

    return None
