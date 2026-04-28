"""
네이버 지도 visitor review GraphQL 크롤러.

비로그인 상태에서 pcmap-api.place.naver.com/graphql 의 getVisitorReviews
오퍼레이션을 직접 호출하여 리뷰를 수집한다.
사업주 로그인 세션 / Selenium / 캡차 토큰에 모두 의존하지 않는다.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://pcmap-api.place.naver.com/graphql"
PAGE_SIZE = 50  # probe 결과 상한 부근. 100+은 서버가 silent reject

# 병원 도메인 카테고리 코드 (브라우저 캡처에서 추출).
# 다른 업종 페이지에서는 다를 수 있으나 hospital 한정으로는 안정적.
HOSPITAL_CID_LIST = ["223175", "223176", "223187", "223260", "223265"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 네이버 내부 query (캡처 기반, 우리에게 필요한 필드만 남김)
QUERY = """query getVisitorReviews($input: VisitorReviewsInput) {
  visitorReviews(input: $input) {
    items {
      id
      cursor
      rating
      body
      visited
      created
      representativeVisitDateTime
      nickname
      originType
      author { nickname }
      media { type thumbnail videoUrl }
      reply { body created date status replyTitle }
    }
    total
  }
}"""


def _build_headers(place_id: str) -> dict:
    """비로그인 호출에 충분한 최소 헤더 셋."""
    return {
        "accept": "*/*",
        "accept-language": "ko",
        "content-type": "application/json",
        "origin": "https://pcmap.place.naver.com",
        "referer": (
            f"https://pcmap.place.naver.com/hospital/{place_id}/review/visitor"
        ),
        "user-agent": USER_AGENT,
    }


def _build_payload(place_id: str, after: Optional[str] = None) -> list[dict]:
    input_vars: dict = {
        "businessId": place_id,
        "businessType": "hospital",
        "item": "0",
        "bookingBusinessId": None,
        "size": PAGE_SIZE,
        "isPhotoUsed": False,
        "includeContent": True,
        "getUserStats": True,
        "includeReceiptPhotos": True,
        "cidList": HOSPITAL_CID_LIST,
        "getReactions": True,
        "getTrailer": True,
    }
    if after:
        input_vars["after"] = after

    return [
        {
            "operationName": "getVisitorReviews",
            "variables": {"input": input_vars},
            "query": QUERY,
        }
    ]


def _parse_iso_utc(dt_str: Optional[str]) -> Optional[datetime]:
    """'2026-04-27T03:53:15.000Z' 형식 ISO 문자열을 naive UTC datetime으로 변환."""
    if not dt_str:
        return None
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        dt = datetime.fromisoformat(dt_str)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def _extract_image_urls(media: list[dict] | None) -> list[str]:
    if not media:
        return []
    return [m["thumbnail"] for m in media if m.get("thumbnail")]


def _normalize_review(item: dict) -> dict:
    """GraphQL item을 _save_reviews(crawler.py)가 기대하는 dict 포맷으로 변환."""
    body = (item.get("body") or "").strip()

    # 닉네임: 최상단 nickname이 비면 author.nickname 폴백
    nickname = (item.get("nickname") or "").strip()
    if not nickname:
        nickname = ((item.get("author") or {}).get("nickname") or "").strip()
    nickname = nickname or "익명"

    # 별점: 방문자 리뷰는 보통 null. 기본 5.0 유지(기존 동작과 동일)
    rating_raw = item.get("rating")
    try:
        rating = float(rating_raw) if rating_raw is not None else 5.0
    except (TypeError, ValueError):
        rating = 5.0

    reply = item.get("reply") or {}
    reply_body = (reply.get("body") or "").strip()
    is_replied = bool(reply_body)

    return {
        "platform": "naver",
        "platform_review_id": item["id"],
        "author": nickname,
        "rating": rating,
        "rating_scale": 5,
        "content": body,
        "image_urls": _extract_image_urls(item.get("media")),
        "reviewed_at": _parse_iso_utc(item.get("representativeVisitDateTime")),
        "is_replied": is_replied,
        "reply_content": reply_body,
    }


def fetch_naver_reviews(place_id: str, max_pages: int = 10) -> list[dict]:
    """
    네이버 지도 visitor reviews를 GraphQL로 수집한다.

    Args:
        place_id: 네이버 지도 Place ID (예: "19528043")
        max_pages: 최대 페이지 수. 페이지당 PAGE_SIZE(=50)건.

    Returns:
        리뷰 dict 리스트 (services.crawler._save_reviews가 기대하는 포맷)
    """
    logger.info(
        f"네이버 리뷰 GraphQL 크롤링 시작: place_id={place_id}, "
        f"max_pages={max_pages}, page_size={PAGE_SIZE}"
    )

    headers = _build_headers(place_id)
    reviews: list[dict] = []
    after: Optional[str] = None

    for page in range(max_pages):
        try:
            resp = requests.post(
                GRAPHQL_URL,
                headers=headers,
                json=_build_payload(place_id, after=after),
                timeout=20,
            )
        except Exception as e:
            logger.error(f"네이버 GraphQL 요청 실패 (page={page}): {e}")
            break

        if resp.status_code != 200:
            logger.error(
                f"네이버 GraphQL 비정상 응답 (page={page}): "
                f"status={resp.status_code} body={resp.text[:200]}"
            )
            break

        try:
            payload = resp.json()
            vr = payload[0]["data"]["visitorReviews"]
        except (ValueError, KeyError, IndexError, TypeError) as e:
            logger.error(f"네이버 GraphQL 응답 파싱 실패 (page={page}): {e}")
            break

        if vr is None:
            logger.warning(f"page={page} visitorReviews=null. 종료")
            break

        items = vr.get("items") or []
        total = vr.get("total")
        if not items:
            logger.info(f"page={page} items=0. 종료")
            break

        for raw in items:
            try:
                # 본문 없는 리뷰(사진/평점 only)는 스킵 — 기존 동작 유지
                if not (raw.get("body") or "").strip():
                    continue
                reviews.append(_normalize_review(raw))
            except Exception as e:
                logger.warning(f"리뷰 정규화 실패: {e}")
                continue

        logger.info(
            f"page={page} +{len(items)}건 (누적={len(reviews)}/total={total})"
        )

        # 다음 페이지 커서 갱신
        after = items[-1].get("cursor")
        if not after:
            logger.info("마지막 cursor 없음. 종료")
            break

        # 응답이 PAGE_SIZE보다 적으면 마지막 페이지
        if len(items) < PAGE_SIZE:
            logger.info(
                f"page={page} items({len(items)}) < PAGE_SIZE({PAGE_SIZE}). 종료"
            )
            break

    logger.info(f"네이버 리뷰 GraphQL 크롤링 완료: {len(reviews)}건")
    return reviews
