from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Alert, Review
from schemas import AlertOut, ReviewOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertWithReview(AlertOut):
    review: Optional[ReviewOut] = None


@router.get("", response_model=list[AlertWithReview])
def list_alerts(
    is_read: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """알림 목록 (최신순)"""
    query = db.query(Alert).options(joinedload(Alert.review)).order_by(desc(Alert.created_at))

    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)

    alerts = query.all()

    # review 관계를 포함하여 반환
    result = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "hospital_id": alert.hospital_id,
            "review_id": alert.review_id,
            "type": alert.type,
            "is_read": alert.is_read,
            "created_at": alert.created_at,
            "review": alert.review,
        }
        result.append(alert_dict)

    return result


@router.patch("/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    """알림 읽음 처리"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return {"detail": "알림을 찾을 수 없습니다."}

    alert.is_read = True
    db.commit()
    return {"message": "읽음 처리 완료"}


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db)):
    """읽지 않은 알림 수"""
    count = db.query(Alert).filter(Alert.is_read == False).count()
    return {"count": count}
