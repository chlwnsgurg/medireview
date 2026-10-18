"""
네이버 댓글 자동 등록 서비스
Selenium으로 네이버 사업주 페이지에서 리뷰에 답글을 등록합니다.
(네이버 로그인은 Chrome 프로필에 이미 되어 있다고 가정)

플로우:
1. naver_review_id로 답글 상세 URL 직접 구성
2. 답글 상세 페이지 이동 → 답글 쓰기 → 등록
"""
import logging
import re
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import settings

logger = logging.getLogger(__name__)


def _create_driver() -> webdriver.Chrome:
    """Chrome 드라이버 생성 (기존 프로필 사용으로 로그인 세션 유지)"""
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


def _is_valid_review_id(naver_review_id: str) -> bool:
    """네이버 리뷰 ID 형식(24자리 hex) 여부.

    해시 폴백 ID(naver_xxx)로 URL을 구성하면 다른 리뷰에 답글이 등록될 수 있으므로 차단합니다.
    """
    return bool(re.fullmatch(r"[a-f0-9]{24}", naver_review_id or ""))


def _build_reply_url(place_id: str, naver_review_id: str) -> str:
    """naver_review_id로 답글 상세 페이지 URL을 직접 구성합니다.

    URL 형식:
    https://new-m.smartplace.naver.com/bizes/place-id/{place_id}/reviews/{review_id}
        ?from=search
        &redirectUrl=https://pcmap.place.naver.com/hospital/{place_id}/review/visitor
    """
    redirect_url = urllib.parse.quote(
        f"https://pcmap.place.naver.com/hospital/{place_id}/review/visitor"
    )
    return (
        f"https://new-m.smartplace.naver.com/bizes/place-id/{place_id}"
        f"/reviews/{naver_review_id}"
        f"?from=search&redirectUrl={redirect_url}"
    )


def _is_on_review_page(driver: webdriver.Chrome, naver_review_id: str) -> bool:
    """리다이렉트 후 실제 도착한 페이지가 대상 리뷰의 상세 페이지인지 확인합니다.

    리뷰를 찾지 못해 목록 등 다른 화면으로 이동하면, 첫 번째 리뷰에 답글이 등록될 수 있으므로 차단합니다.
    """
    path = urllib.parse.urlparse(driver.current_url).path
    if f"/reviews/{naver_review_id}" not in path:
        logger.error(f"대상 리뷰 페이지가 아닙니다 (기대 ID: {naver_review_id}, 현재 URL: {driver.current_url})")
        return False
    return True


def _write_reply(
    driver: webdriver.Chrome, reply_url: str, naver_review_id: str, reply_text: str
) -> bool:
    """답글 상세 페이지에서 답글 작성 및 등록"""
    driver.get(reply_url)
    time.sleep(3)

    if not _is_on_review_page(driver, naver_review_id):
        return False

    try:
        wait = WebDriverWait(driver, 10)

        # "답글 쓰기" 버튼 클릭
        write_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-area-code="rv.replywrite"]')
            )
        )
        write_btn.click()
        time.sleep(1)

        # textarea에 답글 입력
        textarea = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#replyWrite"))
        )
        textarea.click()
        textarea.send_keys(reply_text)
        time.sleep(0.5)

        # "등록" 버튼 클릭
        submit_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-area-code="rv.replydone"]')
            )
        )
        submit_btn.click()
        time.sleep(2)

        logger.info("답글 등록 완료")
        return True

    except Exception as e:
        logger.error(f"답글 작성 중 오류: {e}")
        return False


def post_reply_to_naver(
    place_id: str, naver_review_id: str, reply_text: str
) -> bool:
    """
    네이버 리뷰에 답글을 자동 등록합니다.

    Args:
        place_id: 네이버 지도 Place ID
        naver_review_id: 네이버 리뷰 고유 ID (답글 버튼 URL에서 추출)
        reply_text: 등록할 답글 내용

    Returns:
        성공 여부
    """
    if not _is_valid_review_id(naver_review_id):
        logger.error(f"유효한 naver_review_id가 아니어서 답글을 등록할 수 없습니다: {naver_review_id!r}")
        return False

    if not reply_text or len(reply_text) < 15:
        logger.error("답글은 최소 15자 이상이어야 합니다.")
        return False

    driver = None
    try:
        driver = _create_driver()

        # naver_review_id로 답글 URL 직접 구성
        reply_url = _build_reply_url(place_id, naver_review_id)
        logger.info(f"답글 URL: {reply_url}")

        # 답글 작성 및 등록
        return _write_reply(driver, reply_url, naver_review_id, reply_text)

    except Exception as e:
        logger.error(f"네이버 댓글 등록 실패: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def _edit_reply(
    driver: webdriver.Chrome, reply_url: str, naver_review_id: str, new_text: str
) -> bool:
    """답글 상세 페이지에서 기존 답글을 수정합니다."""
    driver.get(reply_url)
    time.sleep(3)

    if not _is_on_review_page(driver, naver_review_id):
        return False

    try:
        wait = WebDriverWait(driver, 10)

        # 1. "수정" 버튼 클릭 (답글 영역의 수정 링크)
        edit_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a[data-pui-click-code="rv.replyedit"]')
            )
        )
        edit_btn.click()
        time.sleep(1)

        # 2. textarea에서 기존 내용 지우고 새 내용 입력
        textarea = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#replyWrite"))
        )
        textarea.click()
        # 기존 내용 전체 선택 후 교체
        textarea.send_keys(Keys.CONTROL, "a")
        time.sleep(0.3)
        textarea.send_keys(new_text)
        time.sleep(0.5)

        # 3. "수정" 완료 버튼 클릭
        submit_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-area-code="rv.replyeditedit"]')
            )
        )
        submit_btn.click()
        time.sleep(2)

        logger.info("답글 수정 완료")
        return True

    except Exception as e:
        logger.error(f"답글 수정 중 오류: {e}")
        return False


def edit_reply_on_naver(
    place_id: str, naver_review_id: str, new_text: str
) -> bool:
    """
    네이버 리뷰에 등록된 답글을 수정합니다.

    Args:
        place_id: 네이버 지도 Place ID
        naver_review_id: 네이버 리뷰 고유 ID
        new_text: 수정할 답글 내용

    Returns:
        성공 여부
    """
    if not _is_valid_review_id(naver_review_id):
        logger.error(f"유효한 naver_review_id가 아니어서 답글을 수정할 수 없습니다: {naver_review_id!r}")
        return False

    if not new_text or len(new_text) < 15:
        logger.error("답글은 최소 15자 이상이어야 합니다.")
        return False

    driver = None
    try:
        driver = _create_driver()

        # naver_review_id로 답글 URL 직접 구성 (기존 함수 재사용)
        reply_url = _build_reply_url(place_id, naver_review_id)
        logger.info(f"답글 수정 URL: {reply_url}")

        # 답글 수정
        return _edit_reply(driver, reply_url, naver_review_id, new_text)

    except Exception as e:
        logger.error(f"네이버 답글 수정 실패: {e}")
        return False
    finally:
        if driver:
            driver.quit()

