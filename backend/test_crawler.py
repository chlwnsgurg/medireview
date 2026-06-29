"""
네이버 크롤러 테스트 스크립트
실행: cd backend && source venv/bin/activate && python test_crawler.py
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Step 1: Selenium + Chrome 연결 테스트
print("=" * 60)
print("Step 1: Selenium + Chrome 연결 테스트")
print("=" * 60)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    print("  ChromeDriver 설치/확인 중...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print(f"  ✅ Chrome 연결 성공 (버전: {driver.capabilities.get('browserVersion', 'unknown')})")
    driver.quit()
except Exception as e:
    print(f"  ❌ Chrome 연결 실패: {e}")
    sys.exit(1)

# Step 2: 네이버 지도 페이지 접근 테스트
print()
print("=" * 60)
print("Step 2: 네이버 지도 페이지 접근 테스트")
print("=" * 60)

PLACE_ID = "19528043"
url = f"https://pcmap.place.naver.com/hospital/{PLACE_ID}/review/visitor"
print(f"  URL: {url}")

try:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    driver.implicitly_wait(10)

    import time
    time.sleep(5)

    title = driver.title
    page_len = len(driver.page_source)
    print(f"  페이지 제목: {title}")
    print(f"  페이지 소스 길이: {page_len:,} 글자")

    # HTML 일부를 저장해서 셀렉터 확인
    from bs4 import BeautifulSoup
    html = driver.page_source
    bs = BeautifulSoup(html, "lxml")

    # 리뷰 셀렉터 테스트 (실제 fetch_naver_reviews()가 사용하는 셀렉터와 동일하게 유지)
    # 참고: 이 단계는 스크롤/더보기 클릭을 하지 않으므로 lazy-load 전이라 0개로 나올 수 있음.
    #       실제 매칭 여부는 Step 3(크롤러 실행)의 수집 건수로 판단할 것.
    selectors_to_try = [
        ("li.place_apply_pui.EjjAW", "리뷰 항목 (기본)"),
        ("li.EjjAW", "리뷰 항목 (폴백)"),
        ("div.pui__vn15t2", "리뷰 내용 div"),
        ("div.pui__JiVbY3 > span.pui__uslU0d", "작성자 닉네임"),
    ]

    print()
    print("  [셀렉터 매칭 결과]")
    for selector, name in selectors_to_try:
        found = bs.select(selector)
        print(f"    {name} ({selector}): {len(found)}개")

    driver.quit()

    if page_len < 1000:
        print("  ⚠️ 페이지 소스가 너무 짧음 — 차단되었거나 리디렉트된 것일 수 있습니다")
    else:
        print("  ✅ 페이지 접근 성공")

except Exception as e:
    print(f"  ❌ 페이지 접근 실패: {e}")
    sys.exit(1)

# Step 3: 크롤러 함수 실행 테스트
print()
print("=" * 60)
print("Step 3: fetch_naver_reviews() 실행 테스트")
print("=" * 60)

try:
    from services.naver_crawler import fetch_naver_reviews

    print(f"  Place ID: {PLACE_ID}")
    print(f"  더보기 클릭: 최대 3회 (테스트용 제한)")
    print("  크롤링 중... (10~20초 소요)")

    reviews = fetch_naver_reviews(PLACE_ID, max_pages=3)

    print(f"\n  ✅ 수집 결과: {len(reviews)}건")

    if reviews:
        print(f"\n  [샘플 리뷰 (최대 3건)]")
        for i, r in enumerate(reviews[:3]):
            print(f"  --- 리뷰 {i+1} ---")
            print(f"    작성자: {r['author']}")
            print(f"    별점: {r['rating']}/{r['rating_scale']}")
            print(f"    내용: {r['content'][:80]}...")
            print(f"    날짜: {r.get('reviewed_at', 'N/A')}")
            print(f"    이미지: {len(r.get('image_urls', []))}장")
            print(f"    ID: {r['platform_review_id']}")
    else:
        print("  ⚠️ 수집된 리뷰가 없습니다. 셀렉터가 변경되었을 수 있습니다.")
        print("  → HTML 구조를 확인하려면 tmp/debug_page.html 을 저장합니다.")

        # 디버깅용 HTML 저장
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5)
        with open("../tmp/debug_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        print("  → ../tmp/debug_page.html 에 저장 완료")

except Exception as e:
    print(f"  ❌ 크롤러 실행 실패: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("테스트 완료")
print("=" * 60)
