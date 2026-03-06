"""
DB 마이그레이션: reviews 테이블에 reply_content 컬럼 추가

실행: cd backend && python scripts/add_reply_content.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine


def migrate():
    with engine.connect() as conn:
        # 컬럼 존재 여부 확인
        result = conn.execute(
            __import__("sqlalchemy").text("PRAGMA table_info(reviews)")
        )
        columns = [row[1] for row in result]

        if "reply_content" in columns:
            print("reply_content 컬럼이 이미 존재합니다.")
            return

        conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE reviews ADD COLUMN reply_content TEXT DEFAULT ''"
            )
        )
        conn.commit()
        print("reply_content 컬럼 추가 완료")


if __name__ == "__main__":
    migrate()
