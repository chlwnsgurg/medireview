# 프론트엔드 — frontend/src/ 상세

> React 19 + Vite 6 + Tailwind CSS 4 + react-router-dom 7 + Axios
> 14 JSX/JS 파일, ~29KB

---

## 의존성

| 패키지            | 버전  | 용도                   |
| ----------------- | ----- | ---------------------- |
| react             | ^19.0 | UI 프레임워크          |
| react-dom         | ^19.0 | DOM 렌더링             |
| react-router-dom  | ^7.1  | SPA 라우팅             |
| axios             | ^1.7  | HTTP 클라이언트        |
| @tailwindcss/vite | ^4.0  | Tailwind Vite 플러그인 |
| tailwindcss       | ^4.0  | 유틸리티 CSS           |
| vite              | ^6.0  | 빌드 도구              |

---

## 진입점

### main.jsx (230B)

```jsx
ReactDOM.createRoot(document.getElementById('root'))
  .render(<StrictMode><App /></StrictMode>)
```

### App.jsx (24L)

`BrowserRouter` + `Routes` + 5개 라우트 (모두 `Layout` 하위):

| Path           | 컴포넌트             |
| -------------- | -------------------- |
| `/`            | `Dashboard`          |
| `/reviews/:id` | `ReviewDetail`       |
| `/alerts`      | `Alerts`             |
| `/automation`  | `AutomationSettings` |
| `/settings`    | `Settings`           |

---

## api/client.js (38L) — Axios 래퍼

`axios.create({ baseURL: '/api' })` — Vite 프록시로 백엔드 연결.

| 그룹       | 함수                    | Method | 경로                               |
| ---------- | ----------------------- | ------ | ---------------------------------- |
| Hospital   | `getHospital`           | GET    | `/hospital`                        |
|            | `createHospital`        | POST   | `/hospital`                        |
|            | `updateHospital`        | PUT    | `/hospital`                        |
| Reviews    | `getReviews`            | GET    | `/reviews` (params 전달)           |
|            | `getReview`             | GET    | `/reviews/${id}`                   |
|            | `getReviewStats`        | GET    | `/reviews/stats`                   |
|            | `syncReviews`           | POST   | `/reviews/sync`                    |
| Comments   | `generateComments`      | POST   | `/reviews/${id}/generate-comments` |
|            | `getComments`           | GET    | `/reviews/${id}/comments`          |
|            | `postComment`           | POST   | `/reviews/${id}/post-comment`      |
| Alerts     | `getAlerts`             | GET    | `/alerts`                          |
|            | `markAlertRead`         | PATCH  | `/alerts/${id}/read`               |
|            | `getUnreadCount`        | GET    | `/alerts/unread-count`             |
| Automation | `getAutomationRules`    | GET    | `/automation/rules` ⚠️ 미구현       |
|            | `updateAutomationRules` | PUT    | `/automation/rules` ⚠️ 미구현       |
|            | `getAutomationLogs`     | GET    | `/automation/logs` ⚠️ 미구현        |

---

## 컴포넌트 (components/)

### Layout.jsx (2.2KB)

- 상단 네비게이션 바 (로고 + 메뉴 링크 + 알림 배지)
- `<Outlet />` 으로 하위 라우트 렌더링
- 메뉴: 대시보드, 알림, 자동화, 설정
- 알림 배지: `AlertBadge` 컴포넌트 삽입

### ReviewCard.jsx (1.5KB)

리뷰 카드 UI:
- 별점 (`StarRating` 사용)
- 플랫폼 배지 (`PlatformBadge`)
- 미답변 시 빨간 "미답변" 배지
- 리뷰 본문 (50자 truncate)
- 클릭 시 `/reviews/${id}` 이동

### FilterBar.jsx (2.6KB)

필터 컨트롤:
- 플랫폼 select (전체/네이버/모두닥/굿닥)
- 별점 range (최소/최대)
- 답변 여부 select
- 정렬 select (최신순/오래된순/높은별점/낮은별점)
- onChange 콜백으로 부모에 상태 전달

### StarRating.jsx (760B)

`rating`/`scale` 받아 ★/☆ 문자 렌더링. 소수점 반올림.

### PlatformBadge.jsx (540B)

플랫폼별 컬러 배지:
- naver: 초록
- modudoc: 파랑
- goodoc: 보라

### AlertBadge.jsx (529B)

`getUnreadCount()` 호출 → 미읽음 수 빨간 뱃지.
0 이면 숨김.

---

## 페이지 (pages/)

### Dashboard.jsx (6.6KB)

**통계 카드 4종**:
- 총 리뷰 수
- 평균 별점
- 미답변 수
- 플랫폼별 리뷰 수

**리뷰 목록**:
- `FilterBar` 컴포넌트로 필터 적용
- `ReviewCard` 리스트 렌더링
- 페이지네이션 (이전/다음 버튼)
- **동기화 버튼**: `syncReviews()` 호출 → 새 리뷰 즉시 불러옴

**상태 관리**: `useState` + `useEffect` (API 호출)

### ReviewDetail.jsx (7.4KB)

**리뷰 원문 표시**:
- 별점, 플랫폼 배지, 작성자, 작성일
- 리뷰 전체 본문

**AI 댓글 기능**:
1. "AI 댓글 생성" 버튼 → `generateComments(reviewId)` 호출
2. 3종 댓글 카드 표시 (empathy/guidance/apology)
3. 각 카드: 수정 가능 textarea
4. "선택 & 등록" 버튼 → `postComment(reviewId, commentId)` 호출
5. 등록 성공 시 "등록 완료" 상태 표시

**로딩 상태**: 생성 중 스피너 + 등록 중 비활성화

### Alerts.jsx (4.0KB)

- 알림 목록 (최신순)
- 읽음/안읽음 필터 탭
- 클릭 시 `markAlertRead()` + 해당 리뷰 페이지 이동
- 알림 카드: 별점 + 플랫폼 + 작성일 + 읽음 상태 배지

### Settings.jsx (5.4KB)

- 병원 정보 없을 시: 등록 폼 표시
- 기존 정보 있을 시: 수정 폼 표시
- 필드: 병원명, 네이버 Place ID, 톤앤매너 (정중/친근), 알림 기준 별점
- 저장 시 `createHospital()` 또는 `updateHospital()` 호출

### AutomationSettings.jsx (286B)

플레이스홀더. "자동화 설정 기능은 준비 중입니다."

---

## Vite 설정 (vite.config.js)

```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

개발 시 `/api/*` 요청을 FastAPI 백엔드로 프록시.

---

## 미구현/개선 필요 항목

| 항목               | 현재 상태          | 비고                              |
| ------------------ | ------------------ | --------------------------------- |
| 자동화 설정 UI     | 플레이스홀더       | 백엔드 라우터도 미등록            |
| 커스텀 훅 (hooks/) | 빈 디렉토리        | 데이터 패칭 로직 추출 가능        |
| 에러 바운더리      | 미구현             | API 에러 시 UI 처리 미흡          |
| 반응형 레이아웃    | 기본 Tailwind      | 모바일 최적화 개선 여지           |
| 상태 관리          | useState 개별 관리 | 규모 확장 시 Context/Zustand 검토 |
