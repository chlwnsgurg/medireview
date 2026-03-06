# 서비스 모듈 — services/ 상세

> 비즈니스 로직 계층: Gemini AI + 크롤링 + 댓글 등록 + 알림
> 5 파일, 679L total

---

## gemini.py — AI 댓글 생성 (102L)

### 설정

```python
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
```

### SYSTEM_PROMPT

- 역할: 병·의원 리뷰 답변 전문가
- 규칙: 한국어, 100~200자, 재방문 유도
- 3 스타일: `empathy` (공감형), `guidance` (안내형), `apology` (사과형)
- 출력: JSON 배열 only (마크다운 코드블록 허용)

### generate_comments(review_content, review_rating, hospital_name, tone_style)

| 인자             | 타입  | 설명                       |
| ---------------- | ----- | -------------------------- |
| `review_content` | str   | 리뷰 본문                  |
| `review_rating`  | float | 별점                       |
| `hospital_name`  | str   | 병원명                     |
| `tone_style`     | str   | 톤앤매너 (polite/friendly) |

**반환**: `[{"style": "empathy", "content": "..."}, ...]` (빈 리스트 = 실패)

**내부 흐름**:
1. `tone_style` → 한국어 설명 변환 ("정중하고 격식 있는 말투" / "친근하고 부드러운 말투")
2. Gemini API 호출 (`temperature=0.7`, `max_output_tokens=1024`)
3. 응답 텍스트에서 마크다운 코드블록 제거 (```` → 내용만 추출)
4. `json.loads()` 파싱
5. `valid_styles` 검증 + content 존재 확인
6. 3개 미만 시 warning 로그

**에러 처리**:
- `JSONDecodeError` → 빈 리스트 + error 로그
- 기타 Exception → 빈 리스트 + error 로그

---

## crawler.py — 통합 크롤링 (83L)

### _save_reviews(db, hospital_id, raw_reviews) → int

크롤링 결과를 DB에 저장. **중복 제거 + 알림 자동 생성**.

| 단계 | 로직                                       |
| ---- | ------------------------------------------ |
| 1    | `platform_review_id` 기반 중복 체크        |
| 2    | Review 객체 생성 + `db.add()`              |
| 3    | `db.flush()` — ID 할당 (PK auto increment) |
| 4    | `check_and_create_alert(db, review)` 호출  |
| 5    | saved > 0 이면 `db.commit()`               |

> ⚠️ `flush()` → `commit()` 패턴: 알림 생성에 review.id가 필요하므로 flush 먼저

### sync_naver_reviews(db) → int

1. Hospital 존재 + `naver_place_id` 확인
2. `naver_crawler.fetch_naver_reviews()` 호출
3. `_save_reviews()` 로 DB 저장
4. 반환: 신규 저장 건수

### sync_all_reviews(db) → int

모든 플랫폼 동기화 합산.
현재 MVP: 네이버만 활성. 모두닥/굿닥은 주석 처리.

---

## naver_crawler.py — 네이버 지도 크롤러 (213L)

### _create_driver() → webdriver.Chrome

| 옵션                      | 설명                    |
| ------------------------- | ----------------------- |
| `--headless=new`          | 설정에 따라 (기본 True) |
| `--window-size=1920x1080` | 가상 해상도             |
| `--disable-gpu`           | GPU 비활성              |
| `--no-sandbox`            | 리눅스 호환             |
| `--disable-dev-shm-usage` | shared memory 제한 방지 |
| `user-agent`              | Chrome 120 위장         |

`webdriver_manager` 사용: ChromeDriver 자동 설치/캐싱.

### _parse_date(date_str) → Optional[datetime]

4가지 형식 지원:

| 우선순위 | 형식      | 예시                           |
| -------- | --------- | ------------------------------ |
| 1        | 전체 날짜 | `2026년 2월 28일 토요일`       |
| 2        | 점 구분   | `2026.02.25`                   |
| 3        | 상대 날짜 | `3일 전`, `2시간 전`, `5분 전` |
| 4        | 단축 형식 | `2.28.토` (현재 연도 추정)     |
| fallback | 파싱 불가 | 현재 시각 반환                 |

### _generate_review_id(author, content, date_str) → str

`"naver_{MD5(author_content[:50]_date)[:16]}"` — 중복 체크용 해시 ID.

### fetch_naver_reviews(place_id, max_pages=10) → list[dict]

**크롤링 흐름**:
1. `https://pcmap.place.naver.com/hospital/{place_id}/review/visitor` 접속
2. implicit_wait(10) + sleep(3) 페이지 로드 대기
3. PAGE_DOWN 스크롤
4. "더보기" 버튼 `a.fvwqf` 최대 `max_pages`회 클릭
5. `page_source` → BeautifulSoup 파싱
6. `li.place_apply_pui.EjjAW` 또는 `li.EjjAW` 선택

**파싱 요소**:

| 요소   | CSS 셀렉터                                   | 폴백       |
| ------ | -------------------------------------------- | ---------- |
| 닉네임 | `div.pui__JiVbY3 > span.pui__uslU0d`         | "익명"     |
| 본문   | `div.pui__vn15t2 > a` 또는 `div.pui__vn15t2` | ""         |
| 날짜   | `span.pui__gfuUIT` (첫 번째)                 | utcnow     |
| 별점   | `span.pui__YHaOka`                           | 기본 5.0점 |
| 이미지 | `div.pui__MJi___ img`                        | []         |

> ⚠️ CSS 셀렉터는 네이버 UI 업데이트에 매우 취약. 정기 점검 필요.

반환: `[{"platform": "naver", "platform_review_id": "...", ...}]`
빈 내용 리뷰는 제외.

---

## naver_comment_poster.py — 댓글 자동 등록 (225L)

### _create_driver() → webdriver.Chrome

크롤러와 동일 옵션 + **자동화 감지 방어**:
- `--disable-blink-features=AutomationControlled`
- `excludeSwitches: ["enable-automation"]`

### _login_naver(driver) → bool

| 단계 | 로직                                |
| ---- | ----------------------------------- |
| 1    | `settings.NAVER_ID`/`NAVER_PW` 확인 |
| 2    | 로그인 페이지 이동                  |
| 3    | `execute_script`로 ID/PW value 설정 |
| 4    | 로그인 버튼 `#log\\.login` 클릭     |
| 5    | URL에 `nidlogin` 포함 시 실패 판정  |

> ⚠️ `send_keys` 대신 `execute_script`로 값 직접 주입 — 봇 감지 우회
> ⚠️ 2FA 활성화 시 실패. 네이버 보안 설정 확인 필요.

### _find_reply_url(driver, place_id, review_content) → str | None

1. 사업주 리뷰 페이지 이동
2. `li.EjjAW` 리뷰 목록 순회
3. 리뷰 내용 **첫 30자** substring 매칭
4. 매칭 시 `a[data-pui-click-code="reply"]` href 추출

> ⚠️ 30자 매칭은 짧은 리뷰나 유사 리뷰에서 오매칭 가능

### _write_reply(driver, reply_url, reply_text) → bool

1. 답글 URL 이동
2. `WebDriverWait` + `EC.element_to_be_clickable` 대기
3. "답글 쓰기" 버튼 클릭 → textarea 입력 → "등록" 버튼 클릭

셀렉터:
- 답글 쓰기: `button[data-area-code="rv.replywrite"]`
- textarea: `textarea#replyWrite`
- 등록: `button[data-area-code="rv.replydone"]`

### post_reply_to_naver(place_id, review_content, reply_text) → bool

전체 파이프라인: 드라이버 생성 → 로그인 → URL 찾기 → 답글 작성.
최소 답글 길이: **15자**.

---

## alert_service.py — 저평점 알림 (56L)

### check_and_create_alert(db, review) → Alert | None

| 조건                        | 동작                  |
| --------------------------- | --------------------- |
| `review.rating ≤ threshold` | Alert 생성            |
| 이미 Alert 존재             | None 반환 (중복 방지) |
| Hospital 없음               | None 반환             |

기본 threshold: `hospital.alert_threshold` (기본값 2).
