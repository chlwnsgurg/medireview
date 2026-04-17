"""
Ollama 기반 LLM Provider
- /api/chat 엔드포인트 사용
- "format" 필드에 JSON Schema를 전달하여 구조화 출력 유도 (Ollama 0.5+)
"""
from __future__ import annotations

import json
import logging

import httpx

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


class OllamaProvider:
    def __init__(self) -> None:
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        self._timeout = settings.OLLAMA_TIMEOUT_SEC

    def _chat(self, system_prompt: str, user_prompt: str, json_schema: dict) -> str:
        """Ollama /api/chat 호출 — 구조화된 JSON 문자열 반환"""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": json_schema,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048,
            },
        }
        resp = httpx.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]

    def classify_review(self, review_content: str, review_rating: float) -> dict:
        user_prompt = build_classify_user_prompt(review_content, review_rating)
        try:
            content = self._chat(
                system_prompt=CLASSIFY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                json_schema=ClassifyResult.model_json_schema(),
            )
            result = ClassifyResult.model_validate_json(content)
            return {"type": result.type, "reason": result.reason}
        except Exception as e:
            logger.error(f"Ollama 리뷰 분류 실패: {e}")
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
            content = self._chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema=COMMENT_LIST_JSON_SCHEMA,
            )
            raw_comments = json.loads(content)
            return validate_comments(raw_comments, review_type)
        except Exception as e:
            logger.error(f"Ollama API 호출 실패: {e}")
            return []
