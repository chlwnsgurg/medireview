"""
알림 API 라우터
저평점 리뷰 알림 조회, 읽음 처리, 미읽음 수 조회, 승인 처리
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Alert
from schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    """알림 목록 (최신순)"""
    return (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .limit(100)
        .all()
    )


@router.patch("/{alert_id}/read")
def mark_read(alert_id: int, db: Session = Depends(get_db)):
    """알림 읽음 처리"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")

    alert.is_read = True
    db.commit()
    return {"message": "읽음 처리 완료"}


@router.post("/{alert_id}/approve")
def approve_alert(alert_id: int, db: Session = Depends(get_db)):
    """승인 대기 알림 → 댓글 승인 및 네이버 등록"""
    from services.automation_service import approve_comment

    result = approve_comment(db, alert_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db)):
    """미읽음 알림 수"""
    count = db.query(Alert).filter(Alert.is_read == False).count()
    return {"count": count}
