"""
네이버 지도 리뷰 크롤러
참고: navermap_crawler_example.py 기반으로 구현

셀레니움으로 동적 페이지를 로드한 뒤 BeautifulSoup으로 파싱합니다.
"""
import hashlib
import logging
import time
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from config import settings

logger = logging.getLogger(__name__)


def _create_driver() -> webdriver.Chrome:
    """Chrome 드라이버 생성 (사업주 프로필 사용으로 로그인 세션 유지)"""
    options = webdriver.ChromeOptions()
    if settings.CHROME_HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Chrome 사용자 프로필 경로 설정 (로그인 세션 유지)
    if settings.CHROME_USER_DATA_DIR:
        options.add_argument(f"--user-data-dir={settings.CHROME_USER_DATA_DIR}")
    if settings.CHROME_PROFILE_NAME:
        options.add_argument(f"--profile-directory={settings.CHROME_PROFILE_NAME}")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def _parse_date(date_str: str) -> Optional[datetime]:
    """
    날짜 문자열 파싱
    지원 형식:
      - '2026년 2월 28일 토요일' (네이버 방문일 전체 텍스트)
      - '2026.02.25' / '2026.02.25.'
      - '3일 전', '2시간 전', '5분 전' (상대 날짜)
      - '2.28.토' (단축 형식 — 현재 연도 추정)
    """
    date_str = date_str.strip()
    now = datetime.utcnow()

    import re
    from datetime import timedelta

    # 1) "2026년 2월 28일" 형식
    m = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', date_str)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 2) "2026.02.25" 형식
    date_clean = date_str.rstrip(".")
    try:
        if "." in date_clean and len(date_clean) >= 8:
            return datetime.strptime(date_clean, "%Y.%m.%d")
    except ValueError:
        pass

    # 3) 상대 날짜
    if "분 전" in date_str:
        minutes = int("".join(filter(str.isdigit, date_str)) or "0")
        return now - timedelta(minutes=minutes)
    elif "시간 전" in date_str:
        hours = int("".join(filter(str.isdigit, date_str)) or "0")
        return now - timedelta(hours=hours)
    elif "일 전" in date_str:
        days = int("".join(filter(str.isdigit, date_str)) or "0")
        return now - timedelta(days=days)

    # 4) "2.28.토" 단축 형식 — 현재 연도
    m = re.match(r'(\d{1,2})\.(\d{1,2})\.', date_str)
    if m:
        return datetime(now.year, int(m.group(1)), int(m.group(2)))

    return now


def _generate_review_id(author: str, content: str, date_str: str) -> str:
    """리뷰 내용 기반으로 고유 ID 생성 (naver_review_id 추출 실패 시 폴백용)"""
    raw = f"{author}_{content[:50]}_{date_str}"
    return f"naver_{hashlib.md5(raw.encode()).hexdigest()[:16]}"


def _extract_naver_review_id(item) -> str | None:
    """답글 버튼 URL에서 네이버 리뷰 ID를 추출합니다.
    
    답글 버튼 href 예시:
    https://new-m.smartplace.naver.com/bizes/place-id/{place_id}/reviews/{review_id}?...
    """
    import re
    try:
        reply_link = item.select_one('a[data-pui-click-code="reply"]')
        if reply_link and reply_link.get("href"):
            href = reply_link["href"]
            match = re.search(r'/reviews/([a-f0-9]+)', href)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def fetch_naver_reviews(place_id: str, max_pages: int = 10) -> list[dict]:
    """
    네이버 지도에서 리뷰를 크롤링합니다.

    Args:
        place_id: 네이버 지도 Place ID (예: "19528043")
        max_pages: 더보기 클릭 최대 횟수

    Returns:
        리뷰 딕셔너리 리스트
    """
    url = f"https://pcmap.place.naver.com/hospital/{place_id}/review/visitor"
    logger.info(f"네이버 리뷰 크롤링 시작: {url}")

    driver = None
    reviews = []

    try:
        driver = _create_driver()
        driver.get(url)
        driver.implicitly_wait(10)
        time.sleep(3)

        # 페이지 로드 대기 후 스크롤 다운
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(1)

        # "더보기" 버튼 반복 클릭
        for i in range(max_pages):
            try:
                more_btn = driver.find_element(
                    By.CSS_SELECTOR,
                    "a.fvwqf"  # 네이버 지도 더보기 버튼
                )
                more_btn.click()
                time.sleep(0.5)
            except Exception:
                logger.info(f"더보기 버튼 {i}회 클릭 후 종료")
                break

        time.sleep(2)

        # HTML 파싱
        html = driver.page_source
        bs = BeautifulSoup(html, "lxml")

        # 리뷰 항목 선택
        review_items = bs.select("li.place_apply_pui.EjjAW")

        if not review_items:
            # 대체 셀렉터
            review_items = bs.select("li.EjjAW")

        logger.info(f"파싱된 리뷰 수: {len(review_items)}")

        for item in review_items:
            try:
                # 닉네임
                nickname_el = item.select_one("div.pui__JiVbY3 > span.pui__uslU0d")
                author = nickname_el.text.strip() if nickname_el else "익명"

                # 리뷰 내용
                content_el = item.select_one("div.pui__vn15t2 > a")
                if not content_el:
                    content_el = item.select_one("div.pui__vn15t2")
                content = content_el.text.strip() if content_el else ""

                # 날짜 — span.pui__gfuUIT 중 첫 번째(방문일)에서 전체 텍스트 추출
                date_str = ""
                date_spans = item.select("span.pui__gfuUIT")
                if date_spans:
                    # "방문일2.28.토2026년 2월 28일 토요일" 형태
                    date_str = date_spans[0].text.strip()
                reviewed_at = _parse_date(date_str)

                # 별점 (네이버 지도 리뷰는 텍스트 기반 평가가 많음, 별점이 없을 수 있음)
                rating_el = item.select_one("span.pui__YHaOka")
                if rating_el:
                    try:
                        rating = float(rating_el.text.strip())
                    except ValueError:
                        rating = 5.0
                else:
                    rating = 5.0  # 네이버 방문자 리뷰는 별점 없이 텍스트만인 경우 기본 5점

                # 이미지
                img_elements = item.select("div.pui__MJi___ img")
                image_urls = [img.get("src", "") for img in img_elements if img.get("src")]

                # 네이버 리뷰 ID 추출 (답글 버튼 URL에서)
                naver_review_id = _extract_naver_review_id(item)
                if naver_review_id:
                    platform_review_id = naver_review_id
                else:
                    # 답글 버튼이 없는 경우 해시 기반 ID 폴백
                    platform_review_id = _generate_review_id(author, content, date_str)
                    logger.warning(f"답글 버튼 미발견, 해시 ID 사용: {platform_review_id}")

                if content:  # 내용이 있는 리뷰만 수집
                    reviews.append({
                        "platform": "naver",
                        "platform_review_id": platform_review_id,
                        "author": author,
                        "rating": rating,
                        "rating_scale": 5,
                        "content": content,
                        "image_urls": image_urls,
                        "reviewed_at": reviewed_at,
                    })

            except Exception as e:
                logger.warning(f"리뷰 파싱 실패: {e}")
                continue

    except Exception as e:
        logger.error(f"네이버 크롤링 실패: {e}")

    finally:
        if driver:
            driver.quit()

    logger.info(f"네이버 리뷰 크롤링 완료: {len(reviews)}건")
    return reviews
