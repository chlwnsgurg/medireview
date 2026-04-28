"""
네이버 GraphQL 리뷰 크롤러 수동 검증 스크립트.
실행: cd backend && source venv/bin/activate && python test_crawler.py [PLACE_ID]
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

PLACE_ID = sys.argv[1] if len(sys.argv) > 1 else "19528043"

print("=" * 60)
print(f"fetch_naver_reviews(place_id={PLACE_ID}, max_pages=2) 검증")
print("=" * 60)

try:
    from services.naver_crawler import fetch_naver_reviews

    reviews = fetch_naver_reviews(PLACE_ID, max_pages=2)
    print(f"\n수집 결과: {len(reviews)}건\n")

    for i, r in enumerate(reviews[:3]):
        print(f"--- 샘플 {i + 1} ---")
        print(f"  ID         : {r['platform_review_id']}")
        print(f"  작성자      : {r['author']}")
        print(f"  별점       : {r['rating']}/{r['rating_scale']}")
        print(f"  방문일      : {r.get('reviewed_at')}")
        print(f"  이미지     : {len(r.get('image_urls', []))}장")
        print(f"  답글 여부   : {r['is_replied']}")
        if r["is_replied"]:
            print(f"  답글       : {r['reply_content'][:60]}...")
        print(f"  본문       : {r['content'][:80]}...")
        print()

    if not reviews:
        print("⚠ 수집된 리뷰가 없습니다. place_id 또는 GraphQL 응답을 확인하세요.")
        sys.exit(1)

    print("✅ 검증 완료")

except Exception as e:
    print(f"❌ 실패: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
