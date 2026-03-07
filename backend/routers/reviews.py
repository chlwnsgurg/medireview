from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Review, Hospital
from schemas import ReviewOut, ReviewStats, PaginatedReviews, ReviewTypeUpdate

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("", response_model=PaginatedReviews)
def list_reviews(
    platform: Optional[str] = Query(None, description="플랫폼 필터 (naver, modudoc, goodoc)"),
    min_rating: Optional[int] = Query(None, description="최소 별점"),
    max_rating: Optional[int] = Query(None, description="최대 별점"),
    is_replied: Optional[bool] = Query(None, description="답변 여부"),
    sort: str = Query("latest", description="정렬 (latest, oldest, rating_high, rating_low)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """리뷰 목록 조회 (필터 + 페이지네이션)"""
    query = db.query(Review)

    # 필터 적용
    if platform:
        query = query.filter(Review.platform == platform)
    if min_rating is not None:
        query = query.filter(Review.rating >= min_rating)
    if max_rating is not None:
        query = query.filter(Review.rating <= max_rating)
    if is_replied is not None:
        query = query.filter(Review.is_replied == is_replied)

    # 정렬
    sort_map = {
        "latest": Review.reviewed_at.desc(),
        "oldest": Review.reviewed_at.asc(),
        "rating_high": Review.rating.desc(),
        "rating_low": Review.rating.asc(),
    }
    query = query.order_by(sort_map.get(sort, Review.reviewed_at.desc()))

    # 전체 개수
    total = query.count()

    # 페이지네이션
    items = query.offset((page - 1) * size).limit(size).all()

    return PaginatedReviews(total=total, page=page, size=size, items=items)


@router.get("/stats", response_model=ReviewStats)
def review_stats(db: Session = Depends(get_db)):
    """리뷰 통계"""
    total_count = db.query(Review).count()
    unreplied_count = db.query(Review).filter(Review.is_replied == False).count()

    avg_result = db.query(func.avg(Review.rating)).scalar()
    average_rating = round(float(avg_result), 1) if avg_result else 0.0

    # 플랫폼별 통계
    platform_rows = (
        db.query(
            Review.platform,
            func.count(Review.id),
            func.avg(Review.rating),
        )
        .group_by(Review.platform)
        .all()
    )
    platform_stats = [
        {"platform": p, "count": c, "avg_rating": round(float(a), 1)}
        for p, c, a in platform_rows
    ]

    # 별점 분포
    dist_rows = (
        db.query(
            func.cast(Review.rating, type_=func.integer() if False else Review.rating.type),
            func.count(Review.id),
        )
        .group_by(Review.rating)
        .all()
    )
    rating_distribution = {str(int(r)): c for r, c in dist_rows}
    # 빈 별점도 채우기
    for i in range(1, 6):
        rating_distribution.setdefault(str(i), 0)

    return ReviewStats(
        total_count=total_count,
        average_rating=average_rating,
        unreplied_count=unreplied_count,
        platform_stats=platform_stats,
        rating_distribution=rating_distribution,
    )


@router.get("/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """리뷰 상세 조회"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    return review


@router.patch("/{review_id}/review-type", response_model=ReviewOut)
def update_review_type(review_id: int, body: ReviewTypeUpdate, db: Session = Depends(get_db)):
    """리뷰 유형 수동 변경"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    valid_types = {"positive", "complaint", "claim"}
    if body.review_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 유형입니다. ({', '.join(valid_types)})")

    review.review_type = body.review_type
    review.review_type_reason = "관리자 수동 변경"
    db.commit()
    db.refresh(review)
    return review


@router.post("/sync")
def sync_reviews(db: Session = Depends(get_db)):
    """수동 리뷰 동기화 트리거"""
    from services.crawler import sync_all_reviews
    result = sync_all_reviews(db)
    return {"message": "동기화 완료", "new_reviews": result}
