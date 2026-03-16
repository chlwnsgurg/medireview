"""
토큰 암호화/복호화 유틸리티 (Fernet 대칭키 암호화)
"""
import logging

from cryptography.fernet import Fernet, InvalidToken

from config import settings

logger = logging.getLogger(__name__)

_fernet = None


def _get_fernet() -> Fernet:
    """Fernet 인스턴스를 반환 (싱글턴)"""
    global _fernet
    if _fernet is None:
        key = settings.TOKEN_ENCRYPTION_KEY
        if not key:
            raise RuntimeError(
                "TOKEN_ENCRYPTION_KEY가 설정되지 않았습니다. "
                ".env 파일에 키를 추가하세요. "
                "생성 명령: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_token(plain_text: str) -> str:
    """평문 토큰을 암호화하여 반환"""
    if not plain_text:
        return ""
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_token(encrypted_text: str) -> str:
    """암호화된 토큰을 복호화하여 반환"""
    if not encrypted_text:
        return ""
    try:
        return _get_fernet().decrypt(encrypted_text.encode()).decode()
    except InvalidToken:
        logger.error("토큰 복호화 실패 — 암호화 키가 변경되었거나 데이터가 손상됨")
        return ""
