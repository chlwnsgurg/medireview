"""
V1.1 마이그레이션: Hospital 테이블에 카카오 연동 컬럼 추가
"""
import sqlite3
import sys
import os


def migrate(db_path: str = None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), "..", "medireview.db")

    if not os.path.exists(db_path):
        print(f"DB 파일이 존재하지 않습니다: {db_path}")
        print("앱 시작 시 자동 생성되므로, 먼저 서버를 한 번 실행해주세요.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add = [
        ("kakao_access_token", "TEXT"),
        ("kakao_refresh_token", "TEXT"),
        ("kakao_token_expires_at", "DATETIME"),
        ("kakao_notify_enabled", "BOOLEAN DEFAULT 0"),
        ("kakao_user_id", "VARCHAR(50)"),
    ]

    added = 0
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type}")
            print(f"  ✅ {col_name} 컬럼 추가 완료")
            added += 1
        except sqlite3.OperationalError:
            print(f"  ⏭️ {col_name} 컬럼 이미 존재 — 건너뜀")

    conn.commit()
    conn.close()

    print(f"\nV1.1 마이그레이션 완료: {added}개 컬럼 추가됨")


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else None
    migrate(db)
