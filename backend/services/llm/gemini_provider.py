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


class GeminiProvider:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

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

        try:
            response = self._client.models.generate_content(
                model=MODEL_ID,
                contents=system_prompt + "\n\n" + user_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": COMMENT_LIST_JSON_SCHEMA,
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                },
            )
            raw_comments = json.loads(response.text)
            return validate_comments(raw_comments, review_type)
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            return []
