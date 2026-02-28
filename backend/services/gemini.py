"""
Google Gemini API 기반 리뷰 댓글 생성 서비스
"""
import json
import logging

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

# Gemini 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

TONE_MAP = {
    "polite": "정중하고 격식 있는",
    "friendly": "친근하고 따뜻한",
}

STYLE_LABELS = {
    "empathy": "공감 및 감사형",
    "guidance": "안내 및 개선 약속형",
    "apology": "사과 및 해명형",
}


def generate_reply_drafts(
    hospital_name: str,
    tone_style: str,
    platform: str,
    rating: float,
    rating_scale: int,
    review_content: str,
) -> dict[str, str]:
    """
    리뷰에 대한 3종 댓글 초안을 생성합니다.

    Returns:
        { "empathy": "...", "guidance": "...", "apology": "..." }
    """
    tone_desc = TONE_MAP.get(tone_style, "정중한")

    prompt = f"""당신은 병·의원 리뷰에 대한 전문 답변 작성 도우미입니다.

[병원 정보]
- 병원명: {hospital_name}
- 톤앤매너: {tone_desc}

[리뷰 정보]
- 플랫폼: {platform}
- 별점: {rating}/{rating_scale}
- 내용: {review_content}

다음 3가지 스타일의 답변을 JSON 형식으로 작성해주세요:

{{
  "empathy": "공감 및 감사형 답변 (2~4문장)",
  "guidance": "안내 및 개선 약속형 답변 (2~4문장)",
  "apology": "사과 및 해명형 답변 (2~4문장)"
}}

규칙:
- 톤앤매너를 "{tone_desc}" 스타일로 반드시 지켜주세요
- 각 답변은 2~4문장으로 작성하세요
- 병원명을 적절히 사용하세요
- 리뷰 내용에 구체적으로 응답하세요
- JSON만 반환하세요, 다른 텍스트 없이
- 마크다운 코드블록 없이 순수 JSON만 반환하세요"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # 마크다운 코드블록 제거
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])  # 첫 줄(```json) 제거
        if text.endswith("```"):
            text = text[:-3].strip()

        result = json.loads(text)

        # 3개 키 존재 확인
        for key in ("empathy", "guidance", "apology"):
            if key not in result:
                result[key] = f"[{STYLE_LABELS[key]} 댓글 생성 실패]"

        logger.info("Gemini 댓글 생성 성공")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Gemini 응답 JSON 파싱 실패: {e}\n응답: {text[:200]}")
        return _fallback_drafts()
    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        return _fallback_drafts()


def _fallback_drafts() -> dict[str, str]:
    """API 실패 시 기본 템플릿 반환"""
    return {
        "empathy": "소중한 리뷰를 남겨주셔서 감사합니다. 고객님의 의견을 귀담아 듣겠습니다.",
        "guidance": "소중한 의견 감사드립니다. 더 나은 서비스를 위해 개선하겠습니다.",
        "apology": "불편을 드려 죄송합니다. 말씀해 주신 부분을 개선하도록 노력하겠습니다.",
    }
