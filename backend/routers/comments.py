from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Review, Comment, Hospital
from schemas import CommentOut, CommentPostRequest
from services.gemini import generate_reply_drafts

router = APIRouter(prefix="/api/reviews", tags=["comments"])


@router.post("/{review_id}/generate-comments", response_model=list[CommentOut])
def generate_comments(review_id: int, db: Session = Depends(get_db)):
    """AI 댓글 3종 생성"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    hospital = db.query(Hospital).filter(Hospital.id == review.hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="병원 정보가 없습니다.")

    # 기존 댓글 삭제 (재생성 시)
    db.query(Comment).filter(Comment.review_id == review_id, Comment.is_posted == False).delete()
    db.commit()

    # Gemini로 댓글 3종 생성
    drafts = generate_reply_drafts(
        hospital_name=hospital.name,
        tone_style=hospital.tone_style,
        platform=review.platform,
        rating=review.rating,
        rating_scale=review.rating_scale,
        review_content=review.content or "",
    )

    # DB 저장
    comments = []
    for style, content in drafts.items():
        comment = Comment(
            review_id=review_id,
            style=style,
            content=content,
        )
        db.add(comment)
        comments.append(comment)

    db.commit()
    for c in comments:
        db.refresh(c)

    return comments


@router.get("/{review_id}/comments", response_model=list[CommentOut])
def get_comments(review_id: int, db: Session = Depends(get_db)):
    """리뷰별 생성된 댓글 목록"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    return db.query(Comment).filter(Comment.review_id == review_id).all()


@router.post("/{review_id}/post-comment", response_model=CommentOut)
def post_comment(review_id: int, body: CommentPostRequest, db: Session = Depends(get_db)):
    """
    선택한 댓글을 '등록 완료' 처리합니다.
    MVP에서는 사용자가 댓글을 복사하여 직접 플랫폼에 붙여넣는 방식이므로,
    이 API는 DB 상태만 업데이트합니다 (is_posted=True, is_selected=True).
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    comment = db.query(Comment).filter(
        Comment.id == body.comment_id,
        Comment.review_id == review_id,
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    # 해당 리뷰의 다른 댓글은 선택 해제
    db.query(Comment).filter(
        Comment.review_id == review_id,
        Comment.id != comment.id,
    ).update({"is_selected": False})

    # 선택 댓글 상태 업데이트
    comment.is_selected = True
    comment.is_posted = True
    review.is_replied = True

    db.commit()
    db.refresh(comment)

    return comment
