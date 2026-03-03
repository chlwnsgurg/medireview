"""
Gemini AI 댓글 생성 서비스
Google Gemini API를 사용해 리뷰에 대한 3가지 스타일 답변을 생성합니다.
"""
import json
import logging
import re

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

# Gemini 설정
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config=genai.types.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.7,
        max_output_tokens=2048,
    ),
)

SYSTEM_PROMPT = """당신은 병·의원의 리뷰 답변을 작성하는 전문가입니다.
환자가 남긴 리뷰에 대해 병원 원장 또는 관리자 입장에서 정중하게 답변을 작성합니다.

규칙:
- 한국어로 작성
- 100~200자 내외
- 환자의 감정에 공감하면서도 전문적인 톤 유지
- 개인정보나 의료 정보는 포함하지 않기
- 다시 방문을 유도하는 멘트 포함

3가지 스타일로 답변을 생성하세요:
1. empathy (공감형): 환자 감정에 깊이 공감하며 따뜻하게 답변
2. guidance (안내형): 감사 + 병원 서비스/개선 사항 안내 위주
3. apology (사과형): 불편에 대한 진심 어린 사과 + 개선 약속

결과를 반드시 아래 JSON 형식으로만 출력하세요 (다른 텍스트 없이):
[
  {"style": "empathy", "content": "..."},
  {"style": "guidance", "content": "..."},
  {"style": "apology", "content": "..."}
]
"""


def generate_comments(
    review_content: str,
    review_rating: float,
    hospital_name: str,
    tone_style: str = "polite",
) -> list[dict]:
    """
    리뷰에 대한 AI 댓글 3종(공감/안내/사과) 생성

    Returns:
        [{"style": "empathy", "content": "..."}, ...]
    """
    tone_desc = "정중하고 격식 있는 말투" if tone_style == "polite" else "친근하고 부드러운 말투"

    user_prompt = f"""병원명: {hospital_name}
말투 스타일: {tone_desc}
리뷰 별점: {review_rating}점
리뷰 내용: {review_content}

위 리뷰에 대한 3가지 스타일 답변을 JSON으로 생성하세요."""

    try:
        response = model.generate_content(
            SYSTEM_PROMPT + "\n\n" + user_prompt,
        )

        text = response.text.strip()

        # JSON 파싱 (코드블록이 있을 경우 제거)
        if text.startswith("```"):
            text = re.sub(r'^```\w*\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
            text = text.strip()

        comments = json.loads(text)

        # 유효성 검증
        valid_styles = {"empathy", "guidance", "apology"}
        result = []
        for c in comments:
            if c.get("style") in valid_styles and c.get("content"):
                result.append({"style": c["style"], "content": c["content"]})

        if len(result) != 3:
            logger.warning(f"Gemini 응답에서 유효한 댓글 {len(result)}개 (기대: 3개)")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Gemini 응답 JSON 파싱 실패: {e}")
        return []
    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        return []
