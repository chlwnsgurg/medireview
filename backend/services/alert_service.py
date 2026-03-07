"""
알림 서비스
반감 리뷰(컴플레인/클레임) 감지 시 알림을 생성합니다.
"""
import logging

from sqlalchemy.orm import Session

from models import Alert, Review

logger = logging.getLogger(__name__)

# 리뷰 유형 → 알림 타입 매핑
_ALERT_TYPE_MAP = {
    "complaint": "complaint",
    "claim": "claim",
}


def check_and_create_alert(db: Session, review: Review) -> Alert | None:
    """
    리뷰 유형이 컴플레인 또는 클레임이면 알림 생성

    Args:
        db: DB 세션
        review: 저장된 리뷰 객체 (review_type이 설정되어 있어야 함)

    Returns:
        생성된 Alert 또는 None
    """
    alert_type = _ALERT_TYPE_MAP.get(review.review_type)
    if not alert_type:
        return None

    # 중복 알림 체크
    existing = (
        db.query(Alert)
        .filter(Alert.review_id == review.id)
        .first()
    )
    if existing:
        return None

    alert = Alert(
        hospital_id=review.hospital_id,
        review_id=review.id,
        type=alert_type,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    label = "컴플레인" if alert_type == "complaint" else "클레임"
    logger.info(
        f"반감 리뷰 알림 생성: 리뷰#{review.id} ({label}, 별점 {review.rating}점)"
    )
    return alert
