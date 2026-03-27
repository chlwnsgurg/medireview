"""
Gemini AI 댓글 생성 서비스
리뷰 유형 분류 후 유형별 맞춤 프롬프트로 답변 3종을 생성합니다.

google-genai SDK + Pydantic Structured Output 사용
→ response_schema로 JSON 구조를 강제하여 파싱 에러 방지
"""
import logging
from typing import Literal

from google import genai
from pydantic import BaseModel, Field

from config import settings

logger = logging.getLogger(__name__)

# ── Gemini 클라이언트 설정 ─────────────────────────────
client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_ID = "gemini-2.5-flash"


# ── Pydantic 응답 스키마 ──────────────────────────────

class ClassifyResult(BaseModel):
    """리뷰 분류 결과 스키마"""
    type: Literal["positive", "complaint", "claim"]
    reason: str = Field(description="분류 근거를 한 문장으로")


class CommentItem(BaseModel):
    """생성된 댓글 항목 스키마"""
    style: str = Field(description="댓글 스타일 코드")
    content: str = Field(description="댓글 본문 (100~150자)")


# ── 리뷰 유형 분류 ──────────────────────────────────

CLASSIFY_SYSTEM_PROMPT = """당신은 병원 리뷰 분류 전문가입니다.
환자가 남긴 리뷰를 분석하여 아래 3가지 유형 중 하나로 분류하세요.

## 분류 기준

1. positive (호감 리뷰): 만족, 칭찬, 감사를 표현하는 리뷰
2. complaint (컴플레인): 주관적인 감정이나 기대치 미달에 의한 불만
   - 예: 불친절함, 비싼 비용, 분위기 불만 등
3. claim (클레임): 객관적인 기준이나 약속 위반으로 발생한 문제
   - 예: 예약 미준수, 시술 부작용, 잘못된 진료, 위생 문제 등

## 판단 보조 정보
- 별점이 높더라도(4-5점) 내용에 불만이 있으면 내용 기준으로 분류
- 별점이 낮더라도(1-2점) 내용이 긍정적이면 내용 기준으로 분류
- 내용이 없거나 모호한 경우 별점 기준 (4점 이상 positive, 3점 이하 complaint)

결과를 JSON으로 출력하세요."""


def classify_review(review_content: str, review_rating: float) -> dict:
    """
    리뷰를 호감/컴플레인/클레임으로 분류한다.

    Returns:
        {"type": "positive|complaint|claim", "reason": "분류 근거"}
    """
    user_prompt = f"""리뷰 별점: {review_rating}점
리뷰 내용: {review_content or "(내용 없음)"}

위 리뷰를 분류해 주세요."""

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=CLASSIFY_SYSTEM_PROMPT + "\n\n" + user_prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": ClassifyResult.model_json_schema(),
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
        )
        result = ClassifyResult.model_validate_json(response.text)
        return {"type": result.type, "reason": result.reason}

    except Exception as e:
        logger.error(f"리뷰 분류 실패: {e}")
        fallback_type = "positive" if review_rating >= 4 else "complaint"
        return {"type": fallback_type, "reason": "분류 실패, 별점 기반 자동 분류"}


# ── 유형별 프롬프트 ──────────────────────────────────

COMMON_RULES = """## 공통 규칙
- 한국어로 작성
- 100~150자 내외
- 개인정보나 의료 정보는 포함하지 않기
- 리뷰 작성자 이름을 자연스럽게 호칭에 활용
- ⚠️ 리뷰에 오타나 맞춤법 오류가 있을 수 있음
  → 원문을 그대로 인용하지 말고, 전후 문맥을 파악하여 작성자의 의도를 추론한 뒤 답변 작성
  → 예: "달 치료하고 갑니다" → "잘 치료하고 갑니다"로 추론"""

TYPE_PROMPTS = {
    "positive": f"""당신은 병원 리뷰 답변 전문가입니다. 아래는 만족/칭찬을 담은 호감 리뷰입니다.

## 작성 전략
1. 감사 인사: 방문 및 소중한 리뷰에 대한 감사 표현
2. 포인트 강조: 고객이 언급한 장점(친절, 실력, 시설 등)을 한 번 더 언급
3. 재방문 기약: 다음 만남을 기약하며 앞으로의 다짐을 밝힘

## 톤 & 핵심
- 공감과 감사 표현 중심
- 리뷰에 나타난 병원의 서비스와 치료에 대한 구체적인 칭찬 포인트를 답글의 주요 소재로 활용
- 따뜻하고 진심 어린 어조

{COMMON_RULES}

3가지 변형 답변을 생성하세요. 각 답변은 같은 전략을 따르되 표현과 강조점을 다르게 합니다.
style 필드에는 반드시 pos_thanks, pos_highlight, pos_revisit 중 하나를 사용하세요.
결과를 JSON 배열로 출력하세요.""",

    "complaint": f"""당신은 병원 리뷰 답변 전문가입니다. 아래는 주관적 불만을 담은 컴플레인 리뷰입니다.

## 작성 전략: YES - BUT 구조
- YES (언어/감정 복사): 고객이 제시한 문제를 요약하고, 느꼈을 감정에 공감 표현
- BUT (정제된 해명): 오해가 있었던 상황이나 어쩔 수 없었던 배경을 정중하게 설명

## 톤 & 핵심
- 고객의 감정을 먼저 긍정하고 수용
- 정제된 언어로 병원의 입장 설명 및 개선 의지 표명
- 변명이 아닌 설명의 톤

{COMMON_RULES}

3가지 변형 답변을 생성하세요. 각 답변은 YES-BUT 구조를 따르되 강조점을 다르게 합니다.
style 필드에는 반드시 comp_empathy, comp_explain, comp_improve 중 하나를 사용하세요.
결과를 JSON 배열로 출력하세요.""",

    "claim": f"""당신은 병원 리뷰 답변 전문가입니다. 아래는 객관적 사실 기반의 클레임 리뷰입니다.

## 작성 전략: YES - BUT 구조
- YES (언어 복사/사과): 문제를 즉시 인정하고 진정성 있는 사과 및 상황 설명
- BUT (책임감/개선 약속): 재발 방지를 위한 구체적인 대책과 개선 의지 강조

## 톤 & 핵심
- 즉각적이고 진정성 있는 사과
- 문제 회피 없이 책임 인정
- 구체적인 재발 방지 대책 제시
- 무거운 마음을 표현하되 과도한 비굴함은 지양

{COMMON_RULES}

3가지 변형 답변을 생성하세요. 각 답변은 YES-BUT 구조를 따르되 강조점을 다르게 합니다.
style 필드에는 반드시 clm_apology, clm_cause, clm_prevent 중 하나를 사용하세요.
결과를 JSON 배열로 출력하세요.""",
}

VALID_STYLES = {
    "positive": {"pos_thanks", "pos_highlight", "pos_revisit"},
    "complaint": {"comp_empathy", "comp_explain", "comp_improve"},
    "claim": {"clm_apology", "clm_cause", "clm_prevent"},
}


def generate_comments(
    review_content: str,
    review_rating: float,
    review_type: str,
    hospital_name: str,
    tone_style: str = "polite",
    reviewer_name: str = "",
) -> list[dict]:
    """
    유형별 맞춤 프롬프트로 AI 댓글 3종 생성

    Returns:
        [{"style": "pos_thanks", "content": "..."}, ...]
    """
    system_prompt = TYPE_PROMPTS.get(review_type, TYPE_PROMPTS["complaint"])
    tone_desc = "정중하고 격식 있는 말투" if tone_style == "polite" else "친근하고 부드러운 말투"

    user_prompt = f"""병원명: {hospital_name}
말투 스타일: {tone_desc}
리뷰 작성자: {reviewer_name or "고객"}
리뷰 별점: {review_rating}점
리뷰 내용: {review_content or "(내용 없음)"}

위 리뷰에 대한 3가지 변형 답변을 JSON 배열로 생성하세요."""

    # list[CommentItem]에 대한 JSON 스키마 생성
    list_schema = {
        "type": "array",
        "items": CommentItem.model_json_schema(),
    }

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=system_prompt + "\n\n" + user_prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": list_schema,
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
        )
        import json
        raw_comments = json.loads(response.text)

        valid_styles = VALID_STYLES.get(review_type, set())
        result = []
        for c in raw_comments:
            item = CommentItem.model_validate(c)
            if item.style in valid_styles and item.content:
                result.append({"style": item.style, "content": item.content})

        if len(result) != 3:
            logger.warning(f"Gemini 응답에서 유효한 댓글 {len(result)}개 (기대: 3개)")

        return result

    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        return []
