from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import hospital, reviews
from scheduler import start_scheduler, stop_scheduler


# 앱 시작 시 테이블 자동 생성 + 스케줄러 시작
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="MediReview API",
    description="병·의원 통합 리뷰 관리 플랫폼",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정 (프론트엔드 개발 서버 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(hospital.router)
app.include_router(reviews.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
