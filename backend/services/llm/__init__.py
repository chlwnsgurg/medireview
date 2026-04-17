"""
LLM Provider 패키지
환경변수 LLM_PROVIDER에 따라 Gemini 또는 Ollama 프로바이더를 선택한다.

외부에서는 classify_review / generate_comments 두 함수만 사용한다.
"""
from config import settings
from services.llm.base import LLMProvider

_provider: LLMProvider | None = None


def _get_provider() -> LLMProvider:
    global _provider
    if _provider is not None:
        return _provider

    name = (settings.LLM_PROVIDER or "gemini").lower()
    if name == "gemini":
        from services.llm.gemini_provider import GeminiProvider
        _provider = GeminiProvider()
    elif name == "ollama":
        from services.llm.ollama_provider import OllamaProvider
        _provider = OllamaProvider()
    else:
        raise ValueError(f"지원하지 않는 LLM_PROVIDER: {name}")
    return _provider


def classify_review(review_content: str, review_rating: float) -> dict:
    return _get_provider().classify_review(review_content, review_rating)


def generate_comments(
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
    return _get_provider().generate_comments(
        review_content=review_content,
        review_rating=review_rating,
        review_type=review_type,
        hospital_name=hospital_name,
        tone_style=tone_style,
        reviewer_name=reviewer_name,
        region=region,
        description=description,
        seo_keywords=seo_keywords,
    )
