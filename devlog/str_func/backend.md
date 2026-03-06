# 인프라 모듈 — config · database · models · schemas · scheduler

> 의존 0 설정 + 데이터 레이어 + 스케줄러

---

## config.py — 환경 설정 (18L)

`pydantic-settings`의 `BaseSettings` 기반. `.env` 파일에서 자동 로드.

| 필드                    | 타입 | 기본값                      | 설명                           |
| ----------------------- | ---- | --------------------------- | ------------------------------ |
| `DATABASE_URL`          | str  | `sqlite:///./medireview.db` | DB 연결 문자열                 |
| `GEMINI_API_KEY`        | str  | `""`                        | Google Gemini API 키           |
| `SYNC_INTERVAL_MINUTES` | int  | `5`                         | 크롤링 주기 (분)               |
| `NAVER_PLACE_ID`        | str  | `""`                        | 네이버 지도 Place ID (전역)    |
| `CHROME_HEADLESS`       | bool | `True`                      | Selenium headless 모드         |
| `NAVER_ID`              | str  | `""`                        | 네이버 로그인 ID (댓글 등록용) |
| `NAVER_PW`              | str  | `""`                        | 네이버 로그인 PW               |

**싱글턴**: `settings = Settings()` — 모듈 레벨에서 인스턴스 생성, import시 공유.

> ⚠️ `NAVER_ID`/`NAVER_PW`는 네이버 댓글 자동 등록에만 사용. 크롤링은 비로그인.

---

## database.py — DB 연결 (23L)

```python
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

| Export         | 역할                                               |
| -------------- | -------------------------------------------------- |
| `engine`       | SQLAlchemy 엔진 (SQLite `check_same_thread=False`) |
| `SessionLocal` | 세션 팩토리 (autocommit=False)                     |
| `Base`         | 모든 ORM 모델의 상위 클래스                        |
| `get_db()`     | FastAPI `Depends`용 제너레이터 (try/finally close) |

> ⚠️ `check_same_thread=False` — SQLite 전용 옵션. PostgreSQL 전환 시 제거 필요.

---

## models.py — ORM 모델 (95L)

### Hospital (10L)

| 컬럼              | 타입        | 기본값     | 설명               |
| ----------------- | ----------- | ---------- | ------------------ |
| `id`              | Integer PK  | auto       |                    |
| `name`            | String(200) | required   | 병원명             |
| `naver_place_id`  | String(50)  | `""`       | 네이버 Place ID    |
| `tone_style`      | String(20)  | `"polite"` | polite \| friendly |
| `alert_threshold` | Integer     | `2`        | 알림 기준 별점     |
| `created_at`      | DateTime    | utcnow     |                    |

관계: `reviews` (1:N), `alerts` (1:N), `automation_rule` (1:1, uselist=False)

### Review (25L)

| 컬럼                 | 타입        | 기본값   | 설명                       |
| -------------------- | ----------- | -------- | -------------------------- |
| `id`                 | Integer PK  | auto     |                            |
| `hospital_id`        | Integer FK  | required | → hospitals.id             |
| `platform`           | String(20)  | required | naver \| modudoc \| goodoc |
| `platform_review_id` | String(100) | null     | 원본 플랫폼 리뷰 ID        |
| `author`             | String(100) | null     | 작성자                     |
| `rating`             | Float       | required | 별점                       |
| `rating_scale`       | Integer     | `5`      | 5 또는 10                  |
| `content`            | Text        | null     | 리뷰 본문                  |
| `image_urls`         | Text        | `"[]"`   | JSON array                 |
| `reviewed_at`        | DateTime    | null     | 리뷰 작성일                |
| `is_replied`         | Boolean     | `False`  | 답변 여부                  |
| `created_at`         | DateTime    | utcnow   |                            |
| `updated_at`         | DateTime    | utcnow   | onupdate=utcnow            |

관계: `hospital` (N:1), `comments` (1:N), `alerts` (1:N)
프로퍼티: `image_url_list` — `json.loads(image_urls)` 반환

### Comment (12L)

| 컬럼          | 타입       | 기본값   | 설명                           |
| ------------- | ---------- | -------- | ------------------------------ |
| `id`          | Integer PK | auto     |                                |
| `review_id`   | Integer FK | required | → reviews.id                   |
| `style`       | String(20) | required | empathy \| guidance \| apology |
| `content`     | Text       | required | AI 생성 댓글                   |
| `is_selected` | Boolean    | `False`  | 사용자 선택 여부               |
| `is_posted`   | Boolean    | `False`  | 실제 등록 여부                 |
| `created_at`  | DateTime   | utcnow   |                                |

### Alert (12L)

| 컬럼          | 타입       | 기본값         | 설명           |
| ------------- | ---------- | -------------- | -------------- |
| `id`          | Integer PK | auto           |                |
| `hospital_id` | Integer FK | required       | → hospitals.id |
| `review_id`   | Integer FK | required       | → reviews.id   |
| `type`        | String(30) | `"low_rating"` | 알림 유형      |
| `is_read`     | Boolean    | `False`        | 읽음 여부      |
| `created_at`  | DateTime   | utcnow         |                |

### AutomationRule (16L)

| 컬럼               | 타입       | 기본값      | 설명                    |
| ------------------ | ---------- | ----------- | ----------------------- |
| `id`               | Integer PK | auto        |                         |
| `hospital_id`      | Integer FK | required    | → hospitals.id (unique) |
| `is_enabled`       | Boolean    | `False`     | 자동화 활성화           |
| `auto_reply_style` | String(20) | `"empathy"` | 기본 댓글 스타일        |
| `hold_keywords`    | Text       | `"[]"`      | 대응 보류 키워드 JSON   |
| `require_approval` | Boolean    | `False`     | 관리자 승인 필요        |
| `created_at`       | DateTime   | utcnow      |                         |

프로퍼티: `hold_keyword_list` — `json.loads(hold_keywords)` 반환

---

## schemas.py — Pydantic 스키마 15개 (135L)

| 스키마                 | 부모               | 용도                       |
| ---------------------- | ------------------ | -------------------------- |
| `HospitalBase`         | BaseModel          | 공통 필드                  |
| `HospitalCreate`       | HospitalBase       | POST 요청                  |
| `HospitalUpdate`       | BaseModel          | PUT 요청 (모두 Optional)   |
| `HospitalOut`          | HospitalBase       | 응답 (+id, created_at)     |
| `ReviewBase`           | BaseModel          | 공통 필드                  |
| `ReviewOut`            | ReviewBase         | 응답 (+id, hospital_id 등) |
| `CommentBase`          | BaseModel          | 공통 필드                  |
| `CommentOut`           | CommentBase        | 응답 (+id, review_id 등)   |
| `CommentPostRequest`   | BaseModel          | comment_id만               |
| `AlertOut`             | BaseModel          | 알림 응답                  |
| `AutomationRuleBase`   | BaseModel          | 공통 필드                  |
| `AutomationRuleUpdate` | BaseModel          | PUT 요청 (모두 Optional)   |
| `AutomationRuleOut`    | AutomationRuleBase | 응답 (+id, hospital_id)    |
| `ReviewStats`          | BaseModel          | 통계 응답                  |
| `PaginatedReviews`     | BaseModel          | 페이지네이션 응답          |

> 모든 `*Out` 스키마: `Config.from_attributes = True` (SQLAlchemy ORM 호환)

---

## scheduler.py — 리뷰 폴링 잡 (49L)

| 함수                | 역할                                 |
| ------------------- | ------------------------------------ |
| `_sync_job()`       | 독립 SessionLocal → sync_all_reviews |
| `start_scheduler()` | interval 잡 등록 (replace_existing)  |
| `stop_scheduler()`  | shutdown(wait=False)                 |

- `BackgroundScheduler` 사용 (별도 스레드)
- `main.py` lifespan에서 start/stop 호출
- `replace_existing=True` — 중복 잡 방지

---

## seed.py — 더미 데이터 시드 (119L)

| 데이터         | 내용                                  |
| -------------- | ------------------------------------- |
| Hospital       | "서울이비인후과" (place_id: 19528043) |
| AutomationRule | 기본값 (is_enabled=False)             |
| Reviews × 50   | 80% 고평점(3~5), 20% 저평점(1~2)      |
| 리뷰 예시      | 실제 한국어 리뷰 20개 + 저평점 5개    |
| 플랫폼 분포    | naver 60%, modudoc 20%, goodoc 20%    |
| 기간           | 최근 60일 내 랜덤                     |

실행: `cd backend && source venv/bin/activate && python seed.py`
