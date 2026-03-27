"""
V1.0 마이그레이션: 리뷰 유형 분류 시스템 추가

변경 사항:
  - reviews 테이블: review_type, review_type_reason 컬럼 추가
  - automation_rules 테이블: auto_reply_style 제거 → 유형별 변형 컬럼 3개 추가
  - comments.style 기존 값 마이그레이션
"""
import sqlite3
import sys
import os


def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # 1. reviews 테이블에 review_type, review_type_reason 추가
        existing = {row[1] for row in cur.execute("PRAGMA table_info(reviews)").fetchall()}

        if "review_type" not in existing:
            cur.execute("ALTER TABLE reviews ADD COLUMN review_type VARCHAR(20)")
            print("[OK] reviews.review_type 추가")

        if "review_type_reason" not in existing:
            cur.execute("ALTER TABLE reviews ADD COLUMN review_type_reason TEXT")
            print("[OK] reviews.review_type_reason 추가")

        # 2. automation_rules 테이블에 유형별 변형 컬럼 추가
        existing_ar = {row[1] for row in cur.execute("PRAGMA table_info(automation_rules)").fetchall()}

        if "auto_reply_positive_variant" not in existing_ar:
            cur.execute("ALTER TABLE automation_rules ADD COLUMN auto_reply_positive_variant VARCHAR(30) DEFAULT 'pos_thanks'")
            print("[OK] automation_rules.auto_reply_positive_variant 추가")

        if "auto_reply_complaint_variant" not in existing_ar:
            cur.execute("ALTER TABLE automation_rules ADD COLUMN auto_reply_complaint_variant VARCHAR(30) DEFAULT 'comp_empathy'")
            print("[OK] automation_rules.auto_reply_complaint_variant 추가")

        if "auto_reply_claim_variant" not in existing_ar:
            cur.execute("ALTER TABLE automation_rules ADD COLUMN auto_reply_claim_variant VARCHAR(30) DEFAULT 'clm_apology'")
            print("[OK] automation_rules.auto_reply_claim_variant 추가")

        # 3. 기존 comments.style 값 마이그레이션
        style_map = {
            "empathy": "comp_empathy",
            "guidance": "pos_highlight",
            "apology": "clm_apology",
        }
        for old_style, new_style in style_map.items():
            affected = cur.execute(
                "UPDATE comments SET style = ? WHERE style = ?",
                (new_style, old_style),
            ).rowcount
            if affected > 0:
                print(f"[OK] comments.style '{old_style}' → '{new_style}' ({affected}건)")

        conn.commit()
        print("\n마이그레이션 완료!")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] 마이그레이션 실패: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "medireview.db"
    )
    print(f"DB 경로: {db_path}")
    migrate(db_path)
