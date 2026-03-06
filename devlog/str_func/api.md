# API 엔드포인트 — routers/ 상세

> FastAPI REST API 전체 엔드포인트 레퍼런스
> 4개 라우터, 12개 엔드포인트, total 323L

---

## 1. Hospital — `/api/hospital` (54L)

단일 병원 CRUD. MVP에서는 **항상 `db.query(Hospital).first()`** 사용.

### GET `/api/hospital` → HospitalOut

병원 정보 조회. 없으면 404.

### POST `/api/hospital` → HospitalOut (201)

최초 등록. 이미 존재하면 400.
**부수 효과**: AutomationRule도 기본값으로 함께 생성.

### PUT `/api/hospital` → HospitalOut

정보 수정 (partial update). `model_dump(exclude_unset=True)` → `setattr` 반복.

---

## 2. Reviews — `/api/reviews` (118L)

### GET `/api/reviews` → PaginatedReviews

리뷰 목록. 쿼리 파라미터:

| 파라미터     | 타입  | 설명                                                      |
| ------------ | ----- | --------------------------------------------------------- |
| `platform`   | str?  | 플랫폼 필터 (naver, modudoc, goodoc)                      |
| `min_rating` | int?  | 최소 별점                                                 |
| `max_rating` | int?  | 최대 별점                                                 |
| `is_replied` | bool? | 답변 여부                                                 |
| `sort`       | str   | `latest` (기본) / `oldest` / `rating_high` / `rating_low` |
| `page`       | int   | 페이지 (기본 1, ≥1)                                       |
| `size`       | int   | 페이지 크기 (기본 20, 1~100)                              |

응답: `{ total, page, size, items: ReviewOut[] }`

### GET `/api/reviews/stats` → ReviewStats

통계 계산:
- `total_count`: 총 리뷰 수
- `average_rating`: 평균 별점 (소수점 1자리)
- `unreplied_count`: 미답변 수
- `platform_stats`: `[{ platform, count, avg_rating }]`
- `rating_distribution`: `{ "1": 5, "2": 8, ... }` (빈 키도 포함)

### GET `/api/reviews/{review_id}` → ReviewOut

리뷰 상세. 없으면 404.

### POST `/api/reviews/sync`

수동 동기화 트리거. 내부에서 `crawler.sync_all_reviews(db)` 호출.
응답: `{ message, new_reviews: int }`

---

## 3. Comments — `/api/reviews/{id}/*` (108L)

### POST `/api/reviews/{review_id}/generate-comments` → list[CommentOut]

AI 댓글 3종 생성.

**흐름**:
1. 리뷰 존재 확인 (404)
2. Hospital 정보 조회 (톤앤매너)
3. 기존 댓글 **전체 삭제** (`DELETE WHERE review_id=...`)
4. `gemini.generate_comments()` 호출
5. 결과 3개 DB 저장 + refresh
6. 반환

> ⚠️ 기존 댓글이 전부 삭제되므로 이전 세션 댓글 복구 불가

### GET `/api/reviews/{review_id}/comments` → list[CommentOut]

리뷰에 생성된 댓글 목록.

### POST `/api/reviews/{review_id}/post-comment`

선택한 댓글을 **네이버에 자동 등록**.

Body: `{ comment_id: int }`

**흐름**:
1. 리뷰/댓글/병원 존재 확인
2. `naver_place_id` 미설정 시 400
3. `naver_comment_poster.post_reply_to_naver()` 호출
4. 성공 시: `is_selected=True`, `is_posted=True`, `is_replied=True`
5. 실패 시: 500

> ⚠️ Selenium 기반이므로 Chrome 필요. headless 모드 지원.

---

## 4. Alerts — `/api/alerts` (43L)

### GET `/api/alerts` → list[AlertOut]

알림 목록 (최신순, 최대 100건).

### PATCH `/api/alerts/{alert_id}/read`

알림 읽음 처리. 없으면 404.
응답: `{ message: "읽음 처리 완료" }`

### GET `/api/alerts/unread-count`

미읽음 알림 수.
응답: `{ count: int }`

---

## 미구현 API (BLUEPRINT에만 존재)

| Method | Endpoint                | 상태     | 설명                |
| ------ | ----------------------- | -------- | ------------------- |
| GET    | `/api/automation/rules` | ❌ 미구현 | 자동화 규칙 조회    |
| PUT    | `/api/automation/rules` | ❌ 미구현 | 자동화 규칙 수정    |
| GET    | `/api/automation/logs`  | ❌ 미구현 | 자동 대응 로그 조회 |

> `frontend/src/api/client.js`에는 함수가 정의되어 있으나 백엔드 라우터 미등록.
