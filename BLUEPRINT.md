# MediReview — 병·의원 통합 리뷰 관리 플랫폼 MVP 블루프린트

## 1. 구현 범위

| 기능 | 포함 여부 | 설명 |
|------|-----------|------|
| 4.1 리뷰 통합 조회 대시보드 | ✅ MVP | 분산 리뷰 통합 조회, 필터링, 실시간 업데이트 |
| 4.2 AI 댓글 초안 생성 | ✅ MVP | Google Gemini 기반 댓글 3종 생성 |
| 4.3 저평점 리뷰 실시간 알림 | ✅ MVP | 기준 이하 별점 리뷰 알림 (앱 알림) |
| 4.4 악성 리뷰 신고/삭제 요청 | ❌ v2 | 다음 버전에서 구현 |
| 4.5 리뷰 대응 자동화 | ✅ MVP | AI 자동 댓글 등록, 정책 기반 규칙 |

---

## 2. 기술 스택

| 영역 | 기술 | 선정 이유 |
|------|------|-----------|
| **Frontend** | React + Vite | 빠른 빌드, 간결한 설정 |
| **Styling** | Tailwind CSS | 유틸리티 기반 빠른 UI 구축 |
| **Backend** | FastAPI (Python) | 경량, 비동기 지원, 빠른 API 개발 |
| **Database** | SQLite → PostgreSQL | MVP는 SQLite로 시작, 확장 시 PostgreSQL 전환 |
| **ORM** | SQLAlchemy | Python 표준 ORM |
| **AI/LLM** | Google Gemini API | 리뷰 분석 및 댓글 생성 |
| **Task Queue** | APScheduler | 리뷰 폴링 및 알림을 위한 경량 스케줄러 |
| **알림** | 앱 내 알림 (MVP) | MVP에서는 인앱 알림만, 추후 카카오/문자 확장 |

---

## 3. 프로젝트 구조

```
medireview/
├── PROPOSAL.md
├── BLUEPRINT.md
├── frontend/                    # React + Vite
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/                 # API 호출 함수
│       │   └── client.js        # axios/fetch 래퍼
│       ├── components/          # 재사용 컴포넌트
│       │   ├── Layout.jsx
│       │   ├── ReviewCard.jsx
│       │   ├── StarRating.jsx
│       │   ├── FilterBar.jsx
│       │   ├── AlertBadge.jsx
│       │   └── CommentDraft.jsx
│       ├── pages/               # 페이지 컴포넌트
│       │   ├── Dashboard.jsx        # 4.1 리뷰 대시보드
│       │   ├── ReviewDetail.jsx     # 리뷰 상세 + 4.2 AI 댓글
│       │   ├── Alerts.jsx           # 4.3 알림 목록
│       │   ├── AutomationSettings.jsx # 4.5 자동화 설정
│       │   └── Settings.jsx         # 병원 설정
│       └── hooks/
│           └── useReviews.js
│
├── backend/                     # FastAPI
│   ├── requirements.txt
│   ├── main.py                  # FastAPI 앱 엔트리포인트
│   ├── config.py                # 환경변수, 설정
│   ├── database.py              # DB 연결, 세션
│   ├── models.py                # SQLAlchemy 모델
│   ├── schemas.py               # Pydantic 스키마
│   ├── routers/
│   │   ├── reviews.py           # 리뷰 CRUD API
│   │   ├── comments.py          # AI 댓글 생성 API
│   │   ├── alerts.py            # 알림 API
│   │   └── automation.py        # 자동화 규칙 API
│   ├── services/
│   │   ├── crawler.py           # 리뷰 수집 (모두닥, 굿닥, 네이버)
│   │   ├── gemini.py            # Google Gemini API 연동
│   │   ├── alert_service.py     # 저평점 알림 로직
│   │   └── automation_service.py # 자동 대응 로직
│   └── scheduler.py             # APScheduler 리뷰 폴링 잡
│
└── docs/
```

---

## 4. 데이터 모델

### 4.1 ERD 개요

```
Hospital (병원)
├── id (PK)
├── name
├── tone_style          # 톤앤매너 (정중/친근)
├── alert_threshold     # 알림 기준 별점
└── created_at

Review (리뷰)
├── id (PK)
├── hospital_id (FK → Hospital)
├── platform            # modudoc | goodoc | naver
├── platform_review_id  # 원본 플랫폼 리뷰 ID
├── author
├── rating              # 별점 (1~5 또는 1~10)
├── rating_scale        # 5 또는 10
├── content             # 리뷰 본문
├── image_urls          # JSON array
├── reviewed_at         # 리뷰 작성일
├── is_replied          # 댓글 등록 여부
├── created_at
└── updated_at

Comment (AI 생성 댓글)
├── id (PK)
├── review_id (FK → Review)
├── style               # empathy | guidance | apology
├── content             # 생성된 댓글 내용
├── is_selected         # 사용자가 선택했는지
├── is_posted           # 실제 등록 여부
└── created_at

Alert (알림)
├── id (PK)
├── hospital_id (FK → Hospital)
├── review_id (FK → Review)
├── type                # low_rating
├── is_read
└── created_at

AutomationRule (자동화 규칙)
├── id (PK)
├── hospital_id (FK → Hospital)
├── is_enabled          # 자동화 활성화 여부
├── auto_reply_style    # 기본 댓글 스타일
├── hold_keywords       # JSON array — 대응 보류 키워드
├── require_approval    # 관리자 승인 필요 여부
└── created_at
```

---

## 5. API 설계

### 5.1 리뷰 (Reviews)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/reviews` | 리뷰 목록 (필터: platform, rating, date) |
| GET | `/api/reviews/{id}` | 리뷰 상세 |
| GET | `/api/reviews/stats` | 리뷰 통계 (플랫폼별 평균 별점, 개수) |
| POST | `/api/reviews/sync` | 수동 리뷰 동기화 트리거 |

### 5.2 AI 댓글 (Comments)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/reviews/{id}/generate-comments` | AI 댓글 3종 생성 |
| POST | `/api/reviews/{id}/post-comment` | 선택한 댓글을 플랫폼에 등록 |
| GET | `/api/reviews/{id}/comments` | 리뷰별 생성된 댓글 목록 |

### 5.3 알림 (Alerts)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/alerts` | 알림 목록 |
| PATCH | `/api/alerts/{id}/read` | 알림 읽음 처리 |
| GET | `/api/alerts/unread-count` | 읽지 않은 알림 수 |

### 5.4 자동화 (Automation)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/automation/rules` | 현재 자동화 규칙 조회 |
| PUT | `/api/automation/rules` | 자동화 규칙 수정 |
| GET | `/api/automation/logs` | 자동 대응 로그 조회 |

### 5.5 설정 (Settings)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/hospital` | 병원 정보 조회 |
| PUT | `/api/hospital` | 병원 정보 수정 (톤앤매너, 알림 기준 등) |

---

## 6. 핵심 흐름

### 6.1 리뷰 수집 흐름

```
[APScheduler 주기적 실행 (5분 간격)]
    │
    ├─ crawler.py: 모두닥 리뷰 수집
    ├─ crawler.py: 굿닥 리뷰 수집
    └─ crawler.py: 네이버 지도 리뷰 수집
          │
          ▼
    [신규 리뷰 DB 저장]
          │
          ├─ 저평점? → Alert 생성 → 인앱 알림
          │
          └─ 자동화 활성화? → 자동 댓글 생성 → 규칙 체크 → 자동 등록
```

### 6.2 AI 댓글 생성 흐름

```
[사용자: "댓글 생성" 클릭]
    │
    ▼
[Backend: POST /api/reviews/{id}/generate-comments]
    │
    ├─ 리뷰 본문 + 별점 + 병원 톤앤매너 → Gemini API 호출
    │
    ▼
[Gemini: 3종 댓글 생성]
    ├─ 공감 및 감사형
    ├─ 안내 및 개선 약속형
    └─ 사과 및 해명형
    │
    ▼
[사용자: 댓글 선택 → "등록" 클릭]
    │
    ▼
[Backend: 해당 플랫폼에 댓글 등록]
```

### 6.3 자동 대응 흐름

```
[신규 리뷰 감지 & 자동화 활성화됨]
    │
    ▼
[키워드 체크] ─ 보류 키워드 포함? → 대응 보류, 관리자 알림
    │ (통과)
    ▼
[법적 분쟁 가능성 체크] ─ 해당? → 관리자 승인 대기
    │ (통과)
    ▼
[Gemini: 설정된 스타일로 댓글 생성]
    │
    ▼
[자동 등록] → 로그 기록
```

---

## 7. Gemini 프롬프트 설계

### 7.1 댓글 생성 프롬프트 (예시)

```
당신은 병·의원 리뷰에 대한 전문 답변 작성 도우미입니다.

[병원 정보]
- 병원명: {hospital_name}
- 톤앤매너: {tone_style}

[리뷰 정보]
- 플랫폼: {platform}
- 별점: {rating}/{rating_scale}
- 내용: {review_content}

다음 3가지 스타일의 답변을 각각 작성해주세요:

1. **공감 및 감사형**: 환자의 경험에 공감하고 감사를 표현
2. **안내 및 개선 약속형**: 구체적인 개선 계획이나 안내를 포함
3. **사과 및 해명형**: 진심 어린 사과와 함께 상황을 설명

각 답변은 2~4문장으로 작성하세요.
톤앤매너는 "{tone_style}" 스타일로 작성하세요.
```

---

## 8. 페이지 구성

### 8.1 대시보드 (`/`)

- 리뷰 전체 통계 요약 (총 리뷰 수, 평균 별점, 플랫폼별 비율)
- 최신 리뷰 목록 (카드형)
- 필터바: 플랫폼 / 별점 / 기간
- 읽지 않은 알림 배지

### 8.2 리뷰 상세 (`/reviews/:id`)

- 리뷰 원문 표시 (별점, 작성자, 본문, 이미지)
- "AI 댓글 생성" 버튼 → 3종 댓글 표시
- 댓글 선택 후 수정 가능 → "등록" 버튼

### 8.3 알림 (`/alerts`)

- 저평점 리뷰 알림 목록
- 읽음/안읽음 필터
- 클릭 시 해당 리뷰 상세로 이동

### 8.4 자동화 설정 (`/automation`)

- 자동화 ON/OFF 토글
- 기본 댓글 스타일 선택
- 대응 보류 키워드 관리
- 관리자 승인 필요 여부 토글
- 자동 대응 로그 목록

### 8.5 설정 (`/settings`)

- 병원명, 톤앤매너 설정
- 알림 기준 별점 설정

---

## 9. MVP 개발 단계

### Phase 1: 기반 구축 (1주)

- [ ] 프로젝트 초기 설정 (React + Vite, FastAPI)
- [ ] DB 스키마 생성 및 마이그레이션
- [ ] 기본 Layout, 라우팅 설정
- [ ] 병원 설정 CRUD API

### Phase 2: 리뷰 수집 및 대시보드 (1주)

- [ ] 리뷰 크롤러 구현 (모두닥, 굿닥, 네이버)
- [ ] APScheduler 기반 주기적 리뷰 폴링
- [ ] 리뷰 목록/상세 API
- [ ] 대시보드 UI (리뷰 카드, 필터, 통계)

### Phase 3: AI 댓글 및 알림 (1주)

- [ ] Gemini API 연동 및 댓글 생성 서비스
- [ ] 댓글 생성/선택/등록 UI
- [ ] 저평점 알림 로직 구현
- [ ] 알림 페이지 UI

### Phase 4: 자동화 및 마무리 (1주)

- [ ] 자동화 규칙 CRUD
- [ ] 자동 대응 로직 (키워드 필터, 승인 흐름)
- [ ] 자동화 설정 UI
- [ ] 전체 통합 테스트 및 버그 수정

---

## 10. 환경 변수

```env
# Backend
DATABASE_URL=sqlite:///./medireview.db
GEMINI_API_KEY=your-gemini-api-key

# 크롤링 설정
SYNC_INTERVAL_MINUTES=5

# 프론트엔드
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 11. 실행 방법

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
