# devlog/str_func — Source Structure & Function Reference

> 코드 구조 + 함수 레퍼런스 문서 모음. 서브 문서 4개.

## API 엔드포인트 변경 시 동기화 체크리스트

라우터나 API 수정 시 **반드시** 아래를 확인:

### 코드 (3곳)

| #   | 파일                         | 역할            | 확인 사항                        |
| --- | ---------------------------- | --------------- | -------------------------------- |
| 1   | `backend/routers/<name>.py`  | FastAPI 라우터  | endpoint, method, response_model |
| 2   | `frontend/src/api/client.js` | Axios 래퍼      | 엔드포인트 URL + 파라미터 일치   |
| 3   | `backend/schemas.py`         | Pydantic 스키마 | response_model 필드 일치         |

### 크롤러 변경 시

| #   | 파일                                | 확인 사항                  |
| --- | ----------------------------------- | -------------------------- |
| 1   | `backend/services/naver_crawler.py` | CSS 셀렉터, 파싱 로직      |
| 2   | `backend/services/crawler.py`       | 통합 호출, DB 저장 로직    |
| 3   | `backend/services/alert_service.py` | 저평점 알림 threshold 확인 |
| 4   | `backend/scheduler.py`              | 폴링 간격 및 잡 등록       |

### 문서 (3곳)

| #   | 파일                          | 확인 사항                |
| --- | ----------------------------- | ------------------------ |
| 1   | `BLUEPRINT.md`                | API 설계, 데이터 모델    |
| 2   | `PROPOSAL.md`                 | 기능 범위, 비즈니스 모델 |
| 3   | `devlog/str_func/str_func.md` | 파일 트리 + 라인 카운트  |

---

## 서비스 의존 관계

| 서비스                             | 의존 대상                            | 비고                     |
| ---------------------------------- | ------------------------------------ | ------------------------ |
| `config.py`                        | —                                    | 의존 0, 환경 설정        |
| `database.py`                      | config                               | SQLAlchemy 엔진 + 세션   |
| `models.py`                        | database                             | ORM 모델 5개             |
| `schemas.py`                       | —                                    | Pydantic 스키마 (의존 0) |
| `routers/*`                        | database, models, schemas, services  | HTTP 진입점              |
| `services/gemini.py`               | config                               | Gemini API 호출          |
| `services/naver_crawler.py`        | config                               | Selenium 크롤링          |
| `services/naver_comment_poster.py` | config                               | Selenium 댓글 등록       |
| `services/crawler.py`              | models, naver_crawler, alert_service | 통합 크롤링 + DB 저장    |
| `services/alert_service.py`        | models                               | 저평점 알림 생성         |
| `scheduler.py`                     | config, database, crawler            | APScheduler 주기 실행    |
| `main.py`                          | 전체                                 | FastAPI 글루 레이어      |

---

## 새 플랫폼 크롤러 추가 가이드 (예: 모두닥)

### 1. 파일 생성

```
backend/services/modudoc_crawler.py    ← 크롤링 로직
```

### 2. crawler.py 통합

`sync_all_reviews()` 에 호출 추가:
```python
total += sync_modudoc_reviews(db)
```

### 3. 문서 업데이트

위 "문서 3곳" 체크리스트 따라 BLUEPRINT, str_func 등 갱신.
