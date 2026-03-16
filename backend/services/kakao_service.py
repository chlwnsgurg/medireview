"""
카카오톡 알림 서비스
- 토큰 자동 갱신 (리프레시 토큰)
- 나에게 메시지 발송 (기본 텍스트 템플릿)
- 알림 유형별 메시지 템플릿 생성
"""
import json
import logging
from datetime import datetime, timedelta

import requests
from sqlalchemy.orm import Session

from config import settings
from services.encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

KAUTH_HOST = "https://kauth.kakao.com"
KAPI_HOST = "https://kapi.kakao.com"
FRONTEND_URL = "http://localhost:5173"


# ── 토큰 갱신 ────────────────────────────────────────


def refresh_kakao_token(db: Session, hospital) -> bool:
    """
    리프레시 토큰으로 액세스 토큰 갱신
    갱신 성공 시 암호화하여 DB에 저장한다.

    Returns: 갱신 성공 여부
    """
    refresh_token = decrypt_token(hospital.kakao_refresh_token)
    if not refresh_token:
        logger.warning("리프레시 토큰이 없어 갱신 불가")
        return False

    data = {
        "grant_type": "refresh_token",
        "client_id": settings.KAKAO_CLIENT_ID,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
        "refresh_token": refresh_token,
    }

    try:
        resp = requests.post(f"{KAUTH_HOST}/oauth/token", data=data, timeout=10)
    except requests.RequestException as e:
        logger.error(f"카카오 토큰 갱신 요청 실패: {e}")
        return False

    if resp.status_code != 200:
        logger.error(f"카카오 토큰 갱신 실패 [{resp.status_code}]: {resp.text}")
        return False

    token_data = resp.json()

    hospital.kakao_access_token = encrypt_token(token_data["access_token"])

    # 리프레시 토큰이 새로 발급된 경우에만 갱신
    if "refresh_token" in token_data:
        hospital.kakao_refresh_token = encrypt_token(token_data["refresh_token"])

    expires_in = token_data.get("expires_in", 7200)
    hospital.kakao_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    db.commit()
    logger.info("카카오 액세스 토큰 갱신 완료")
    return True


# ── 토큰 유효성 확인 ──────────────────────────────────


def _ensure_valid_token(db: Session, hospital) -> str | None:
    """
    토큰 만료 여부를 확인하고, 만료 시 자동 갱신한다.

    Returns: 복호화된 유효한 액세스 토큰, 실패 시 None
    """
    if not hospital.kakao_access_token:
        return None

    # 만료 확인 (1분 여유)
    if hospital.kakao_token_expires_at:
        if hospital.kakao_token_expires_at < datetime.utcnow() + timedelta(minutes=1):
            logger.info("카카오 액세스 토큰 만료 임박 — 갱신 시도")
            if not refresh_kakao_token(db, hospital):
                return None

    access_token = decrypt_token(hospital.kakao_access_token)
    if not access_token:
        logger.warning("카카오 액세스 토큰 복호화 실패")
        return None

    return access_token


# ── 메시지 발송 ───────────────────────────────────────


def send_kakao_alert(
    db: Session,
    hospital,
    title: str,
    message: str,
    link_path: str = "/",
) -> bool:
    """
    카카오톡 '나에게 보내기'로 알림 메시지 발송

    카카오 API: POST /v2/api/talk/memo/default/send
    참고: tmp/login_and_message_example/api.py - message()

    Args:
        db: DB 세션 (토큰 갱신 시 커밋용)
        hospital: Hospital 모델 객체
        title: 메시지 제목
        message: 메시지 본문
        link_path: 클릭 시 이동할 앱 내 경로

    Returns: 발송 성공 여부
    """
    if not hospital.kakao_notify_enabled:
        return False

    access_token = _ensure_valid_token(db, hospital)
    if not access_token:
        logger.warning("카카오 토큰이 유효하지 않아 메시지 발송 불가")
        return False

    # 기본 텍스트 메시지 템플릿
    template_object = {
        "object_type": "text",
        "text": f"[{title}]\n\n{message}",
        "link": {
            "web_url": f"{FRONTEND_URL}{link_path}",
            "mobile_web_url": f"{FRONTEND_URL}{link_path}",
        },
        "button_title": "MediReview에서 확인",
    }

    headers = {"Authorization": f"Bearer {access_token}"}
    data = {"template_object": json.dumps(template_object)}

    try:
        resp = requests.post(
            f"{KAPI_HOST}/v2/api/talk/memo/default/send",
            headers=headers,
            data=data,
            timeout=10,
        )

        if resp.status_code == 200:
            logger.info(f"카카오톡 알림 발송 성공: {title}")
            return True
        else:
            logger.error(f"카카오톡 알림 발송 실패 [{resp.status_code}]: {resp.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"카카오톡 알림 발송 중 오류: {e}")
        return False


# ── 메시지 템플릿 ─────────────────────────────────────


def build_alert_message(alert_type: str, review=None, reason: str = "") -> tuple[str, str, str]:
    """
    알림 유형에 따른 카카오톡 메시지 생성

    Args:
        alert_type: 알림 유형 (complaint, claim, automation_held, approval_needed)
        review: Review 모델 객체 (optional)
        reason: 보류 사유 등 추가 정보

    Returns: (title, message, link_path)
    """
    content_preview = ""
    if review and review.content:
        content_preview = review.content[:50] + ("..." if len(review.content) > 50 else "")

    link_path = f"/reviews/{review.id}" if review else "/alerts"

    templates = {
        "complaint": (
            "🟠 컴플레인 리뷰 감지",
            f'"{review.author or "익명"}"님이 {review.platform}에 {review.rating}점 리뷰를 남겼습니다.\n"{content_preview}"'
            if review else "컴플레인 리뷰가 감지되었습니다.",
        ),
        "claim": (
            "🔴 클레임 리뷰 감지",
            f'"{review.author or "익명"}"님이 {review.platform}에 {review.rating}점 리뷰를 남겼습니다.\n"{content_preview}"'
            if review else "클레임 리뷰가 감지되었습니다.",
        ),
        "automation_held": (
            "🚫 자동 대응 보류",
            f"키워드가 감지되어 자동 대응이 보류되었습니다.\n사유: {reason}",
        ),
        "approval_needed": (
            "⏳ AI 댓글 승인 대기",
            "AI 댓글이 생성되었습니다. 승인이 필요합니다.",
        ),
    }

    default = ("🔔 MediReview 알림", "새로운 알림이 있습니다.")
    title, message = templates.get(alert_type, default)

    return title, message, link_path
