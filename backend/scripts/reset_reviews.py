"""
기존 리뷰 데이터 초기화 스크립트
naver_review_id 도입으로 인해 기존 해시 기반 ID 리뷰를 삭제합니다.

실행: cd backend && python scripts/reset_reviews.py
"""
import sys
import os

# backend 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Review, Comment, Alert


def reset_reviews():
    db = SessionLocal()
    try:
        # 관련 댓글, 알림 먼저 삭제
        comment_count = db.query(Comment).delete()
        alert_count = db.query(Alert).delete()
        review_count = db.query(Review).delete()
        db.commit()

        print(f"삭제 완료:")
        print(f"  - 리뷰: {review_count}건")
        print(f"  - 댓글: {comment_count}건")
        print(f"  - 알림: {alert_count}건")

    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("모든 리뷰, 댓글, 알림을 삭제합니다. 계속하시겠습니까? (y/N): ")
    if confirm.lower() == "y":
        reset_reviews()
    else:
        print("취소되었습니다.")
