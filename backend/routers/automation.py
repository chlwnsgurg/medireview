"""
자동화 API 라우터
자동화 규칙 CRUD, 자동 대응 로그 조회, 관리자 승인
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import AutomationRule, AutomationLog, Hospital, Comment, Review, Alert
from schemas import AutomationRuleOut, AutomationRuleUpdate, AutomationLogOut
from services.automation_service import batch_auto_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.get("/rules", response_model=AutomationRuleOut)
def get_rules(db: Session = Depends(get_db)):
    """자동화 규칙 조회"""
    hospital = db.query(Hospital).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="병원 정보가 없습니다.")

    rule = db.query(AutomationRule).filter(
        AutomationRule.hospital_id == hospital.id
    ).first()

    if not rule:
        # 기본 규칙 자동 생성
        rule = AutomationRule(hospital_id=hospital.id)
        db.add(rule)
        db.commit()
        db.refresh(rule)

    return rule


@router.put("/rules", response_model=AutomationRuleOut)
def update_rules(body: AutomationRuleUpdate, db: Session = Depends(get_db)):
    """자동화 규칙 수정"""
    hospital = db.query(Hospital).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="병원 정보가 없습니다.")

    rule = db.query(AutomationRule).filter(
        AutomationRule.hospital_id == hospital.id
    ).first()

    if not rule:
        rule = AutomationRule(hospital_id=hospital.id)
        db.add(rule)
        db.flush()

    was_disabled = not rule.is_enabled

    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(rule, k, v)

    db.commit()
    db.refresh(rule)

    # 자동화가 비활성 → 활성으로 변경된 경우 미답변 리뷰 소급 처리
    if was_disabled and rule.is_enabled:
        try:
            batch_result = batch_auto_reply(db)
            logger.info(f"자동화 활성화 소급 처리: {batch_result}")
        except Exception as e:
            logger.error(f"자동화 활성화 소급 처리 실패: {e}")

    return rule


@router.post("/batch-auto-reply")
def run_batch_auto_reply(db: Session = Depends(get_db)):
    """미답변 리뷰 일괄 자동 대응 (최대 100건)"""
    result = batch_auto_reply(db)
    return result


@router.get("/logs", response_model=list[AutomationLogOut])
def get_logs(db: Session = Depends(get_db)):
    """자동 대응 로그 목록 (최신순)"""
    return (
        db.query(AutomationLog)
        .order_by(AutomationLog.created_at.desc())
        .limit(100)
        .all()
    )
