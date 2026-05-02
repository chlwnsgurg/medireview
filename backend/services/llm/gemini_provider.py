"""
Gemini (google-genai) 기반 LLM Provider
"""
from __future__ import annotations

import json
import logging

from google import genai

from config import settings
from services.llm.base import (
    CLASSIFY_SYSTEM_PROMPT,
    COMMENT_LIST_JSON_SCHEMA,
    ClassifyResult,
    TYPE_PROMPTS,
    build_classify_user_prompt,
    build_generate_user_prompt,
    classify_fallback,
    validate_comments,
)

logger = logging.getLogger(__name__)

MODEL_ID = "gemini-2.5-flash"

# 댓글 생성용 토큰 한도. truncation으로 JSON 파싱 실패 시
# 다음 값으로 점진 증가시키며 최대 3회(첫 시도 + 재시도 2회) 호출.
# Gemini 2.5 thinking 토큰까지 max_output_tokens에 포함되므로 여유를 둔다.
GENERATE_TOKEN_BUDGETS = [4096, 8192, 12288]


class GeminiProvider:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    def _finish_reason(response) -> str | None:
        try:
            reason = response.candidates[0].finish_reason
        except (AttributeError, IndexError):
            return None
        if reason is None:
            return None
        return reason.name if hasattr(reason, "name") else str(reason)

    def classify_review(self, review_content: str, review_rating: float) -> dict:
        user_prompt = build_classify_user_prompt(review_content, review_rating)
        try:
            response = self._client.models.generate_content(
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
            logger.error(f"Gemini 리뷰 분류 실패: {e}")
            return classify_fallback(review_rating)

    def generate_comments(
        self,
        review_content: str,
        review_rating: float,
        review_type: str,
        hospital_name: str,
        tone_style: str = "polite",
        reviewer_name: str = "",
        region: str = "",
        description: str = "",
        seo_keywords: str = "",
    ) -> list[dict]:
        system_prompt = TYPE_PROMPTS.get(review_type, TYPE_PROMPTS["complaint"])
        user_prompt = build_generate_user_prompt(
            review_content=review_content,
            review_rating=review_rating,
            hospital_name=hospital_name,
            tone_style=tone_style,
            reviewer_name=reviewer_name,
            region=region,
            description=description,
            seo_keywords=seo_keywords,
        )

        contents = system_prompt + "\n\n" + user_prompt
        last_parse_err: json.JSONDecodeError | None = None

        for attempt, max_tokens in enumerate(GENERATE_TOKEN_BUDGETS, start=1):
            try:
                response = self._client.models.generate_content(
                    model=MODEL_ID,
                    contents=contents,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": COMMENT_LIST_JSON_SCHEMA,
                        "temperature": 0.7,
                        "max_output_tokens": max_tokens,
                    },
                )
            except Exception as e:
                # 네트워크/인증 등 비-truncation 오류는 재시도해도 의미 없음
                logger.error(f"Gemini API 호출 실패 (attempt={attempt}): {e}")
                return []

            finish_reason = self._finish_reason(response)
            if finish_reason and finish_reason != "STOP":
                logger.warning(
                    "Gemini 응답 비정상 종료 "
                    f"(attempt={attempt}, max_tokens={max_tokens}, finish_reason={finish_reason})"
                )

            try:
                raw_comments = json.loads(response.text)
                return validate_comments(raw_comments, review_type)
            except json.JSONDecodeError as e:
                last_parse_err = e
                logger.warning(
                    "Gemini 응답 JSON 파싱 실패 "
                    f"(attempt={attempt}, max_tokens={max_tokens}, finish_reason={finish_reason}): {e}"
                )

        logger.error(
            f"Gemini 댓글 생성 {len(GENERATE_TOKEN_BUDGETS)}회 시도 모두 실패: {last_parse_err}"
        )
        return []
