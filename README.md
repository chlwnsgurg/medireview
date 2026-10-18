# 🏥 MediReview — 병·의원 통합 리뷰 관리 플랫폼

병·의원 정보 제공 플랫폼(네이버 지도 등)에 분산된 고객 리뷰를 **한 곳에서 통합 관리**하고,  
**AI 기반 댓글 생성 · 자동 대응**까지 지원하는 병·의원 전용 리뷰 관리 플랫폼입니다.

---

## 📋 주요 기능

| 기능 | 설명 |
|------|------|
| **리뷰 통합 대시보드** | 네이버 지도 리뷰를 자동 수집하여 별점·날짜별 필터링 및 통계 제공 |
| **AI 댓글 생성** | LLM이 리뷰 맥락에 맞는 댓글 초안 3종(공감형·안내형·사과형) 자동 생성 (로컬 Ollama / Gemini 선택) |
| **네이버 자동 댓글 등록** | 생성된 댓글을 Selenium으로 네이버에 직접 등록 |
| **저평점 리뷰 알림** | 기준 이하 별점 리뷰 즉시 알림 |
| **자동 대응 규칙** | 키워드 보류, 관리자 승인, 완전 자동 등록 등 세밀한 규칙 설정 |
| **자동화 로그** | 모든 자동 대응 이력(승인 대기·보류·등록 완료) 추적 |

---

## 🏗️ 기술 스택

### Backend
- **Framework**: FastAPI 0.115.0
- **Language**: Python 3.12
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite
- **AI**: 로컬 Ollama (`gemma4`, 기본값) / Google Gemini API (`gemini-2.5-flash`) — `LLM_PROVIDER`로 전환
- **크롤링**: Selenium 4.25 + BeautifulSoup4
- **스케줄러**: APScheduler (60분 주기 자동 수집·자동 대응, `SYNC_INTERVAL_MINUTES`로 조정)

### Frontend
- **Framework**: React 19 + Vite 7
- **스타일링**: Tailwind CSS 4
- **라우팅**: React Router DOM 7
- **HTTP**: Axios

---

## 📁 프로젝트 구조

```
medireview/
├── backend/
│   ├── main.py                # FastAPI 앱 진입점
│   ├── config.py              # 환경 설정 (pydantic-settings)
│   ├── database.py            # SQLAlchemy 엔진/세션
│   ├── models.py              # DB 모델 (6개 테이블)
│   ├── schemas.py             # Pydantic 스키마
│   ├── scheduler.py           # APScheduler 설정
│   ├── routers/
│   │   ├── hospital.py        # 병원 CRUD API
│   │   ├── reviews.py         # 리뷰 조회/동기화 API
│   │   ├── comments.py        # AI 댓글 생성/등록 API
│   │   ├── alerts.py          # 알림 조회/승인 API
│   │   └── automation.py      # 자동화 규칙/로그 API
│   ├── services/
│   │   ├── naver_crawler.py   # 네이버 지도 리뷰 크롤러 (Selenium)
│   │   ├── crawler.py         # 크롤링 오케스트레이터
│   │   ├── llm/               # LLM 프로바이더 (분류·댓글 생성)
│   │   │   ├── base.py        #   공용 프롬프트/스키마/검증
│   │   │   ├── ollama_provider.py  #   로컬 Ollama
│   │   │   └── gemini_provider.py  #   Google Gemini API
│   │   ├── naver_comment_poster.py  # 네이버 댓글 자동 등록
│   │   ├── alert_service.py   # 저평점 알림 생성
│   │   └── automation_service.py    # 자동 대응 엔진
│   ├── .env                   # 환경 변수
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # 라우터 설정
│   │   ├── api/client.js      # API 클라이언트 (Axios)
│   │   ├── components/
│   │   │   └── Layout.jsx     # 공통 레이아웃 + 사이드바
│   │   └── pages/
│   │       ├── Dashboard.jsx          # 대시보드 (통계+리뷰 목록)
│   │       ├── ReviewDetail.jsx       # 리뷰 상세 + AI 댓글
│   │       ├── Alerts.jsx             # 알림 목록 + 승인 버튼
│   │       ├── AutomationSettings.jsx # 자동화 규칙 설정 + 로그
│   │       └── Settings.jsx           # 병원 설정
│   ├── package.json
│   └── vite.config.js
│
├── PROPOSAL.md                # 서비스 기획서
├── BLUEPRINT.md               # 개발 설계서
└── README.md
```

---

## 🗄️ DB 스키마

| 테이블 | 설명 |
|--------|------|
| `hospitals` | 병원 정보 (이름, 네이버 Place ID, 톤앤매너, 알림 기준) |
| `reviews` | 수집된 리뷰 (플랫폼, 별점, 내용, 답변 여부) |
| `comments` | AI 생성 댓글 (스타일, 선택 여부, 등록 여부) |
| `alerts` | 알림 (저평점, 보류, 승인 대기) |
| `automation_rules` | 자동화 규칙 (활성화, 스타일, 보류 키워드, 승인 필요 여부) |
| `automation_logs` | 자동 대응 이력 (액션, 상태, 사유) |

---

## 🚀 실행 방법

### 0. 로컬 LLM (Ollama) 준비

```bash
# 설치 (미설치 시)
curl -fsSL https://ollama.com/install.sh | sh

# 모델 다운로드 및 서버 확인
ollama pull gemma4
curl http://localhost:11434/api/tags
```

> GPU 8GB 이상 권장. VRAM이 부족하면 더 작은 모델(`gemma4:4b` 등)로 `OLLAMA_MODEL`을 바꾸세요.

### 1. Backend

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cat > .env << EOF
# LLM: 로컬 Ollama 사용 (API 비용 없음)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:latest
OLLAMA_TIMEOUT_SEC=300

# LLM_PROVIDER=gemini 로 전환 시에만 필요
# GEMINI_API_KEY=your_gemini_api_key

DATABASE_URL=sqlite:///./medireview.db
SYNC_INTERVAL_MINUTES=60
NAVER_ID=your_naver_id
NAVER_PW=your_naver_pw
EOF

# 서버 실행
uvicorn main:app --port 8000 --reload
```

### 2. Frontend

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

---

## 📡 API 엔드포인트

### 병원
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/hospital` | 병원 정보 조회 |
| POST | `/api/hospital` | 병원 등록 |
| PUT | `/api/hospital` | 병원 정보 수정 |

### 리뷰
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/reviews` | 리뷰 목록 (필터+페이지네이션) |
| GET | `/api/reviews/{id}` | 리뷰 상세 |
| GET | `/api/reviews/stats` | 리뷰 통계 |
| POST | `/api/reviews/sync` | 네이버 리뷰 수동 동기화 |

### AI 댓글
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/reviews/{id}/generate-comments` | AI 댓글 3종 생성 |
| GET | `/api/reviews/{id}/comments` | 생성된 댓글 조회 |
| POST | `/api/reviews/{id}/post-comment` | 네이버에 댓글 등록 |

### 알림
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/alerts` | 알림 목록 |
| PATCH | `/api/alerts/{id}/read` | 읽음 처리 |
| POST | `/api/alerts/{id}/approve` | 승인 (자동 대응 댓글 등록) |
| GET | `/api/alerts/unread-count` | 미읽은 알림 수 |

### 자동화
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/automation/rules` | 자동화 규칙 조회 |
| PUT | `/api/automation/rules` | 자동화 규칙 수정 (활성화 시 미답변 소급 처리) |
| POST | `/api/automation/batch-auto-reply` | 미답변 리뷰 일괄 자동 대응 (최대 100건) |
| GET | `/api/automation/logs` | 자동화 로그 조회 |

---

## ⚙️ 자동 대응 흐름

```
신규 리뷰 수집
    │
    ▼
자동화 규칙 확인 (is_enabled?)
    │
    ├─ 비활성 → 종료
    │
    ▼
보류 키워드 체크
    │
    ├─ 키워드 포함 → 보류 (held) + 알림 생성
    │
    ▼
Gemini AI 댓글 생성
    │
    ▼
승인 필요 여부 (require_approval?)
    │
    ├─ Yes → 승인 대기 (pending_approval) + 알림 생성
    │         └─ 관리자 승인 → 네이버 등록
    │
    └─ No → 자동 등록 (posted)
```

---

## 📄 라이선스

이 프로젝트는 학습 및 포트폴리오 목적으로 제작되었습니다.
