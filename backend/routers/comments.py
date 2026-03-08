"""
댓글 API 라우터
AI 리뷰 분류 + 유형별 댓글 생성, 조회, 네이버 댓글 등록
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Review, Comment, Hospital
from schemas import CommentOut, CommentPostRequest, CommentUpdateRequest, GenerateCommentsResponse
from services.gemini import generate_comments

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reviews", tags=["comments"])


@router.post("/{review_id}/generate-comments", response_model=GenerateCommentsResponse)
def api_generate_comments(review_id: int, db: Session = Depends(get_db)):
    """리뷰 유형 분류 후 맞춤 AI 댓글 3종 생성"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    hospital = db.query(Hospital).first()
    hospital_name = hospital.name if hospital else "병원"
    tone_style = hospital.tone_style if hospital else "polite"

    # 기존 생성된 댓글 삭제 (재생성)
    db.query(Comment).filter(Comment.review_id == review_id).delete()
    db.commit()

    if not review.review_type:
        raise HTTPException(status_code=400, detail="리뷰 유형이 분류되지 않았습니다. 리뷰 동기화를 먼저 실행해주세요.")

    # 유형별 맞춤 댓글 생성
    raw_comments = generate_comments(
        review_content=review.content or "",
        review_rating=review.rating,
        review_type=review.review_type,
        hospital_name=hospital_name,
        tone_style=tone_style,
        reviewer_name=review.author or "",
    )

    if not raw_comments:
        raise HTTPException(status_code=500, detail="AI 댓글 생성에 실패했습니다.")

    # DB 저장
    saved = []
    for c in raw_comments:
        comment = Comment(
            review_id=review_id,
            style=c["style"],
            content=c["content"],
        )
        db.add(comment)
        saved.append(comment)

    db.commit()
    for c in saved:
        db.refresh(c)

    return GenerateCommentsResponse(
        review_type=review.review_type,
        review_type_reason=review.review_type_reason or "",
        comments=[CommentOut.model_validate(c) for c in saved],
    )


@router.get("/{review_id}/comments", response_model=list[CommentOut])
def get_comments(review_id: int, db: Session = Depends(get_db)):
    """리뷰의 댓글 목록 조회"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    return db.query(Comment).filter(Comment.review_id == review_id).all()


@router.patch("/{review_id}/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    review_id: int, comment_id: int, body: CommentUpdateRequest, db: Session = Depends(get_db)
):
    """AI 생성 댓글 내용 수정"""
    comment = db.query(Comment).filter(
        Comment.id == comment_id, Comment.review_id == review_id
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.is_posted:
        raise HTTPException(status_code=400, detail="이미 등록된 댓글은 수정할 수 없습니다.")
    comment.content = body.content
    db.commit()
    db.refresh(comment)
    return comment


@router.post("/{review_id}/post-comment")
def post_comment(review_id: int, body: CommentPostRequest, db: Session = Depends(get_db)):
    """선택한 댓글을 네이버에 자동 등록"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    comment = db.query(Comment).filter(Comment.id == body.comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    hospital = db.query(Hospital).first()
    if not hospital or not hospital.naver_place_id:
        raise HTTPException(status_code=400, detail="병원 네이버 Place ID가 설정되지 않았습니다.")

    # 네이버 댓글 자동 등록
    from services.naver_comment_poster import post_reply_to_naver

    # naver_review_id 확인 (해시 기반 ID는 답글 등록 불가)
    naver_review_id = review.platform_review_id or ""
    if naver_review_id.startswith("naver_"):
        raise HTTPException(
            status_code=400,
            detail="이 리뷰는 naver_review_id가 없어 답글을 등록할 수 없습니다. 리뷰를 다시 크롤링해주세요.",
        )

    success = post_reply_to_naver(
        place_id=hospital.naver_place_id,
        naver_review_id=naver_review_id,
        reply_text=comment.content,
    )

    if not success:
        raise HTTPException(status_code=500, detail="네이버 댓글 등록에 실패했습니다.")

    # 상태 업데이트
    comment.is_selected = True
    comment.is_posted = True
    review.is_replied = True
    review.reply_content = comment.content
    db.commit()

    return {"message": "댓글이 성공적으로 등록되었습니다.", "comment_id": comment.id}
