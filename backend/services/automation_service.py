"""
자동 대응 서비스
신규 리뷰에 대해 자동화 규칙에 따라 AI 댓글을 생성하고 등록합니다.

플로우:
  신규 리뷰 → 자동화 ON? → 보류 키워드? → AI 댓글 생성
  → 승인 필요? → 자동 등록 or 승인 대기
"""
import json
import logging

from sqlalchemy.orm import Session

from models import (
    Alert,
    AutomationLog,
    AutomationRule,
    Comment,
    Hospital,
    Review,
)
from services.gemini import generate_comments

logger = logging.getLogger(__name__)


def process_auto_reply(db: Session, hospital: Hospital, review: Review) -> None:
    """
    신규 리뷰에 대해 자동화 규칙을 적용합니다.

    Args:
        db: DB 세션
        hospital: 병원 객체
        review: 신규 저장된 리뷰 객체
    """
    # 1. 자동화 규칙 조회
    rule = (
        db.query(AutomationRule)
        .filter(AutomationRule.hospital_id == hospital.id)
        .first()
    )
    if not rule or not rule.is_enabled:
        return

    # 2. 보류 키워드 체크
    hold_keywords = json.loads(rule.hold_keywords or "[]")
    review_text = (review.content or "").lower()
    for keyword in hold_keywords:
        if keyword.lower() in review_text:
            _create_log(db, hospital.id, review.id, None,
                        action="held", status="held",
                        reason=f"보류 키워드: {keyword}")
            _create_alert(db, hospital.id, review.id, None,
                          alert_type="automation_held")
            logger.info(f"자동 대응 보류: 리뷰#{review.id} (키워드: {keyword})")
            return

    # 3. AI 댓글 생성
    raw_comments = generate_comments(
        review_content=review.content or "",
        review_rating=review.rating,
        hospital_name=hospital.name,
        tone_style=hospital.tone_style,
    )
    if not raw_comments:
        _create_log(db, hospital.id, review.id, None,
                    action="auto_reply", status="failed",
                    reason="AI 댓글 생성 실패")
        logger.error(f"자동 대응 실패: 리뷰#{review.id} — AI 생성 실패")
        return

    # 설정된 스타일의 댓글 선택
    target_style = rule.auto_reply_style or "empathy"
    selected = None
    for c in raw_comments:
        if c["style"] == target_style:
            selected = c
            break
    if not selected:
        selected = raw_comments[0]

    # DB에 댓글 저장
    comment = Comment(
        review_id=review.id,
        style=selected["style"],
        content=selected["content"],
    )
    db.add(comment)
    db.flush()

    # 4. 승인 필요 여부 체크
    if rule.require_approval:
        comment.is_selected = True
        _create_log(db, hospital.id, review.id, comment.id,
                    action="approval_needed", status="pending_approval")
        _create_alert(db, hospital.id, review.id, comment.id,
                      alert_type="approval_needed")
        db.commit()
        logger.info(f"자동 대응 승인 대기: 리뷰#{review.id} 댓글#{comment.id}")
        return

    # 5. 자동 등록 (네이버)
    from services.naver_comment_poster import post_reply_to_naver

    success = post_reply_to_naver(
        place_id=hospital.naver_place_id,
        naver_review_id=review.platform_review_id or "",
        reply_text=comment.content,
    )

    if success:
        comment.is_selected = True
        comment.is_posted = True
        review.is_replied = True
        _create_log(db, hospital.id, review.id, comment.id,
                    action="auto_reply", status="posted")
        logger.info(f"자동 대응 완료: 리뷰#{review.id} 댓글#{comment.id}")
    else:
        _create_log(db, hospital.id, review.id, comment.id,
                    action="auto_reply", status="failed",
                    reason="네이버 댓글 등록 실패")
        logger.error(f"자동 대응 실패: 리뷰#{review.id} — 네이버 등록 실패")

    db.commit()


def approve_comment(db: Session, alert_id: int) -> dict:
    """
    관리자가 알림 페이지에서 승인하면 댓글을 네이버에 등록합니다.

    Args:
        alert_id: approval_needed 타입 Alert ID

    Returns:
        결과 dict
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return {"success": False, "message": "알림을 찾을 수 없습니다."}

    if alert.type != "approval_needed":
        return {"success": False, "message": "승인 대상 알림이 아닙니다."}

    comment = db.query(Comment).filter(Comment.id == alert.comment_id).first()
    if not comment:
        return {"success": False, "message": "댓글을 찾을 수 없습니다."}

    review = db.query(Review).filter(Review.id == alert.review_id).first()
    hospital = db.query(Hospital).filter(Hospital.id == alert.hospital_id).first()

    if not review or not hospital:
        return {"success": False, "message": "리뷰/병원 정보를 찾을 수 없습니다."}

    # 네이버 등록
    from services.naver_comment_poster import post_reply_to_naver

    success = post_reply_to_naver(
        place_id=hospital.naver_place_id,
        naver_review_id=review.platform_review_id or "",
        reply_text=comment.content,
    )

    if success:
        comment.is_posted = True
        review.is_replied = True
        alert.is_read = True

        # 로그 업데이트
        log = (
            db.query(AutomationLog)
            .filter(
                AutomationLog.review_id == review.id,
                AutomationLog.status == "pending_approval",
            )
            .first()
        )
        if log:
            log.status = "approved"

        db.commit()
        return {"success": True, "message": "댓글이 승인되어 네이버에 등록되었습니다."}
    else:
        return {"success": False, "message": "네이버 댓글 등록에 실패했습니다."}


def _create_log(
    db: Session,
    hospital_id: int,
    review_id: int,
    comment_id: int | None,
    action: str,
    status: str,
    reason: str | None = None,
) -> AutomationLog:
    """자동화 로그 생성"""
    log = AutomationLog(
        hospital_id=hospital_id,
        review_id=review_id,
        comment_id=comment_id,
        action=action,
        status=status,
        reason=reason,
    )
    db.add(log)
    return log


def _create_alert(
    db: Session,
    hospital_id: int,
    review_id: int,
    comment_id: int | None,
    alert_type: str,
) -> Alert:
    """자동화 관련 알림 생성"""
    alert = Alert(
        hospital_id=hospital_id,
        review_id=review_id,
        comment_id=comment_id,
        type=alert_type,
    )
    db.add(alert)
    return alert
