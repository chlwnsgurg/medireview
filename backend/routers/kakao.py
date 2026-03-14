"""
카카오 OAuth 및 알림 API 라우터
- 카카오 로그인 (OAuth 2.0 인가 코드 방식)
- 토큰 저장/해제
- 테스트 메시지 발송
"""
import logging
from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Hospital
from services.encryption import encrypt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kakao", tags=["kakao"])

KAUTH_HOST = "https://kauth.kakao.com"
KAPI_HOST = "https://kapi.kakao.com"


@router.get("/authorize")
def kakao_authorize():
    """카카오 로그인 페이지로 리다이렉트"""
    if not settings.KAKAO_CLIENT_ID:
        raise HTTPException(status_code=500, detail="KAKAO_CLIENT_ID가 설정되지 않았습니다.")

    scope = "talk_message"
    authorize_url = (
        f"{KAUTH_HOST}/oauth/authorize"
        f"?response_type=code"
        f"&client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return RedirectResponse(url=authorize_url)


@router.get("/redirect")
def kakao_redirect(code: str, db: Session = Depends(get_db)):
    """
    카카오 OAuth 콜백
    인가 코드 → 토큰 발급 → Hospital에 암호화 저장
    """
    # 1. 토큰 발급
    token_data = _exchange_code_for_token(code)

    # 2. 사용자 프로필 조회
    profile = _get_kakao_profile(token_data["access_token"])

    # 3. Hospital 업데이트 (단일 병원)
    hospital = db.query(Hospital).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="병원 정보가 없습니다. 먼저 병원을 등록하세요.")

    hospital.kakao_access_token = encrypt_token(token_data["access_token"])
    hospital.kakao_refresh_token = encrypt_token(token_data.get("refresh_token", ""))
    expires_in = token_data.get("expires_in", 7200)
    hospital.kakao_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    hospital.kakao_user_id = str(profile["id"])
    hospital.kakao_notify_enabled = True
    db.commit()

    logger.info(f"카카오 연동 완료: kakao_user_id={profile['id']}")

    # 프론트엔드 설정 페이지로 리다이렉트
    return RedirectResponse(url="http://localhost:5173/settings?kakao=connected")


@router.post("/disconnect")
def kakao_disconnect(db: Session = Depends(get_db)):
    """카카오 연동 해제"""
    hospital = db.query(Hospital).first()
    if not hospital or not hospital.kakao_access_token:
        raise HTTPException(status_code=400, detail="카카오 연동 상태가 아닙니다.")

    # 카카오 연결 끊기 API 호출
    from services.encryption import decrypt_token
    access_token = decrypt_token(hospital.kakao_access_token)
    if access_token:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            requests.post(f"{KAPI_HOST}/v1/user/unlink", headers=headers, timeout=10)
        except requests.RequestException:
            logger.warning("카카오 연결 끊기 API 호출 실패 — 로컬 데이터만 삭제")

    hospital.kakao_access_token = None
    hospital.kakao_refresh_token = None
    hospital.kakao_token_expires_at = None
    hospital.kakao_user_id = None
    hospital.kakao_notify_enabled = False
    db.commit()

    logger.info("카카오 연동 해제 완료")
    return {"message": "카카오 연동이 해제되었습니다."}


@router.post("/test-message")
def send_test_message(db: Session = Depends(get_db)):
    """카카오톡 테스트 메시지 발송"""
    from services.kakao_service import send_kakao_alert

    hospital = db.query(Hospital).first()
    if not hospital or not hospital.kakao_access_token:
        raise HTTPException(status_code=400, detail="카카오 연동이 필요합니다.")

    success = send_kakao_alert(
        db=db,
        hospital=hospital,
        title="🔔 MediReview 테스트 알림",
        message="카카오톡 알림이 정상적으로 연동되었습니다.",
        link_path="/settings",
    )

    if not success:
        raise HTTPException(status_code=500, detail="메시지 발송 실패")

    return {"message": "테스트 메시지가 발송되었습니다."}


# ── 내부 헬퍼 함수 ──────────────────────────────────

def _exchange_code_for_token(code: str) -> dict:
    """인가 코드 → 액세스/리프레시 토큰 교환"""
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_CLIENT_ID,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
        "code": code,
    }
    resp = requests.post(f"{KAUTH_HOST}/oauth/token", data=data, timeout=10)
    if resp.status_code != 200:
        logger.error(f"카카오 토큰 발급 실패: {resp.text}")
        raise HTTPException(status_code=400, detail="카카오 토큰 발급 실패")
    return resp.json()


def _get_kakao_profile(access_token: str) -> dict:
    """카카오 사용자 프로필 조회"""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(f"{KAPI_HOST}/v2/user/me", headers=headers, timeout=10)
    if resp.status_code != 200:
        logger.error(f"카카오 프로필 조회 실패: {resp.text}")
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 조회 실패")
    return resp.json()
