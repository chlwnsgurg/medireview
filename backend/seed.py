"""
더미 리뷰 데이터 시드 스크립트
실행: cd backend && source venv/bin/activate && python seed.py
"""
import random
from datetime import datetime, timedelta

from database import Base, engine, SessionLocal
from models import Hospital, Review, AutomationRule

# 실제 리뷰 예시 (review_examples 기반)
SAMPLE_REVIEWS = [
    "턱 수염 제모와 얼굴 점 3개 제거했어요. 깨끗한 병원에서 꼼꼼히 살펴주셔서 잘 마치고 왔네요. 얼른 제모 완료되면 좋겠네요. 감사합니다.",
    "편평사마귀가 점점 번지는 듯하여 방문하게 되었어요! 이왕이면 집근처에서 꼼꼼히 봐주시는 곳을 원했는데 원장님 간호사분들 넘넘 친절하시고! 마취크림 아낌없이 듬뿍 발라주셨어요!",
    "봉침 맞으면 효과가 좋아요 다른부위도 맞아보았고 이번엔 어깨 맞고 갑니다~~감사합니다",
    "그동안 바쁘고 귀찮아서 미뤄왔던 편평사마귀 제거.. 지인 추천으로 큰맘먹고 방문했는데.. 선생님과 간호사분 너무 친절하시고 여러번 방문없이 한번에 목에 있던 편평사마귀 싹 제거했네요.",
    "쥐젖 제거할게 많아서 여기저기 알아보고왔는데 원장선생님도 친절하시고 꼼꼼하게 잘 봐주셨어요! 간호사님들도 너무 친절하세요!",
    "이벤트 행사로 얼굴이랑 목에 쥐젖 제거하고 이뻐지려구요~ 저렴해서 너무 좋네요",
    "원장님 침술이 유명하셔서 자주 방문하는데 올 때마다 만족해요 믿고 가셔도 좋은 곳이에요 원장님과 직원분들도 너무 친절해요~♡",
    "직원분들과 원장님 정말 친절하시고 얼굴전체 목 겨드랑이까지 사마귀, 쥐젖 제거 했는데 하나 빠짐없이 꼼꼼하게 해주세요 같이 하면서 일부 추가 할인도 받아서 너무 만족 합니다",
    "진료를 꼼꼼하게 봐주셔서 정말 좋았습니다. 설명도 자세하게 해주셔서 이해가 잘 되었어요.",
    "대기 시간이 좀 길었지만 진료는 만족스러웠습니다. 다음에도 방문하겠습니다.",
    "친절하게 설명해주시고 치료 후 관리법도 잘 알려주셨어요. 감사합니다!",
    "예약하고 갔는데도 대기가 너무 길었습니다. 진료 자체는 괜찮았는데 대기 시간이 아쉽네요.",
    "처음 방문했는데 생각보다 훨씬 친절하시고 꼼꼼하게 봐주셨어요. 추천합니다!",
    "시술이 빠르고 깔끔하게 잘 되었습니다. 통증도 거의 없었어요.",
    "주차가 좀 불편했지만 병원 시설은 깨끗하고 좋았습니다.",
    "원장님이 정말 실력이 좋으세요. 다른 병원에서 안 낫던 게 여기서 치료되었습니다.",
    "가격이 좀 비싼 편이지만 그만큼 결과가 좋았어요. 만족합니다.",
    "직원분이 불친절했어요. 진료는 괜찮았는데 첫인상이 별로였습니다.",
    "재방문입니다. 지난번에 좋아서 또 왔어요. 역시 만족스럽네요.",
    "아이 데리고 갔는데 원장님이 아이한테도 너무 친절하게 대해주셨어요. 감사합니다.",
]

# 저평점 리뷰
LOW_RATING_REVIEWS = [
    "대기 시간이 너무 길었습니다. 예약 시간을 지켜주셨으면 합니다.",
    "진료가 너무 짧았어요. 제대로 봐주신 건지 의문입니다.",
    "직원 태도가 별로였습니다. 개선이 필요해 보여요.",
    "비용이 예상보다 훨씬 비쌌어요. 사전 안내가 부족했습니다.",
    "시술 후 부작용이 생겼는데 사후 관리가 미흡했습니다.",
]

SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권"]


def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 기존 데이터 삭제
        db.query(Review).delete()
        db.query(AutomationRule).delete()
        db.query(Hospital).delete()
        db.commit()

        # 병원 생성
        hospital = Hospital(
            name="장생한의원",
            naver_place_id="19528043",
            tone_style="polite",
            alert_threshold=2,
        )
        db.add(hospital)
        db.commit()
        db.refresh(hospital)

        # 자동화 규칙 생성
        rule = AutomationRule(hospital_id=hospital.id)
        db.add(rule)

        # 리뷰 생성 (50개)
        now = datetime.utcnow()
        reviews = []

        for i in range(50):
            days_ago = random.randint(0, 60)
            review_date = now - timedelta(days=days_ago, hours=random.randint(0, 23))

            # 80%는 고평점, 20%는 저평점
            if random.random() < 0.2:
                rating = random.choice([1, 2])
                content = random.choice(LOW_RATING_REVIEWS)
            else:
                rating = random.choice([3, 4, 4, 5, 5, 5])
                content = random.choice(SAMPLE_REVIEWS)

            author = f"{random.choice(SURNAMES)}**"
            platform = random.choice(["naver", "naver", "naver", "modudoc", "goodoc"])

            review = Review(
                hospital_id=hospital.id,
                platform=platform,
                platform_review_id=f"{platform}_review_{i+1:04d}",
                author=author,
                rating=float(rating),
                rating_scale=5,
                content=content,
                image_urls="[]",
                reviewed_at=review_date,
                is_replied=random.random() < 0.3,
            )
            reviews.append(review)

        db.add_all(reviews)
        db.commit()

        print(f"✅ 시드 데이터 생성 완료:")
        print(f"   - 병원: {hospital.name} (naver_place_id: {hospital.naver_place_id})")
        print(f"   - 리뷰: {len(reviews)}건")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
