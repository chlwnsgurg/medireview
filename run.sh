#!/usr/bin/env bash

set -euo pipefail

# --- 터미널 출력용 색상 및 스타일 정의 ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

cleanup() {
  # ✅ 핵심: cleanup이 다시 호출되지 않도록 trap을 즉시 해제합니다.
  trap - EXIT INT TERM

  local exit_code=$?
  echo -e "\n${YELLOW}[INFO] 서버를 종료하는 중입니다...${NC}"

  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  
  echo -e "${GREEN}[INFO] 종료 완료. 안녕히 가세요! 👋${NC}"
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

if [[ ! -d "$BACKEND_DIR" || ! -d "$FRONTEND_DIR" ]]; then
  echo -e "${RED}[ERROR] backend 또는 frontend 디렉토리를 찾을 수 없습니다.${NC}"
  exit 1
fi

echo -e "${CYAN}▶ 백엔드 실행 준비 중...${NC}"
(
  cd "$BACKEND_DIR"

  if [[ -f "venv/bin/activate" ]]; then
    source "venv/bin/activate"
  fi

  uvicorn main:app --host 0.0.0.0 --port 9001 --reload
) &
BACKEND_PID=$!

echo -e "${CYAN}▶ 프론트엔드 실행 준비 중...${NC}"
(
  cd "$FRONTEND_DIR"
  npm run dev
) &
FRONTEND_PID=$!

# 백엔드와 프론트엔드가 초기 구동 로그를 출력할 시간을 줍니다.
sleep 3

# 로그와 구분되도록 시각적인 배너를 출력합니다.
echo -e "\n${GREEN}${BOLD}==================================================${NC}"
echo -e "${GREEN}${BOLD}   🚀 개발 서버가 성공적으로 실행되었습니다!      ${NC}"
echo -e "${GREEN}${BOLD}==================================================${NC}"
echo -e "   🔸 ${BOLD}Frontend Web:${NC} ${BLUE}http://localhost:5173${NC}"
echo -e "   🔹 ${BOLD}Backend API:${NC}  ${BLUE}http://localhost:9001${NC}"
echo ""
echo -e "   💡 ${YELLOW}${BOLD}중지하려면 터미널에서 Ctrl+C를 누르세요.${NC}"
echo -e "${GREEN}${BOLD}==================================================${NC}\n"

wait -n "$BACKEND_PID" "$FRONTEND_PID"