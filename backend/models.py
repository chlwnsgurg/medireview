import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    naver_place_id = Column(String(50), default="")  # 네이버 지도 Place ID
    tone_style = Column(String(20), default="polite")  # polite | friendly
    alert_threshold = Column(Integer, default=2)  # 기본 2점 이하 알림
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="hospital")
    alerts = relationship("Alert", back_populates="hospital")
    automation_rule = relationship("AutomationRule", back_populates="hospital", uselist=False)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    platform = Column(String(20), nullable=False)  # modudoc | goodoc | naver
    platform_review_id = Column(String(100))
    author = Column(String(100))
    rating = Column(Float, nullable=False)
    rating_scale = Column(Integer, default=5)  # 5 또는 10
    content = Column(Text)
    image_urls = Column(Text, default="[]")  # JSON array
    reviewed_at = Column(DateTime)
    is_replied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hospital = relationship("Hospital", back_populates="reviews")
    comments = relationship("Comment", back_populates="review")
    alerts = relationship("Alert", back_populates="review")

    @property
    def image_url_list(self):
        return json.loads(self.image_urls) if self.image_urls else []


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    style = Column(String(20), nullable=False)  # empathy | guidance | apology
    content = Column(Text, nullable=False)
    is_selected = Column(Boolean, default=False)
    is_posted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("Review", back_populates="comments")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    type = Column(String(30), default="low_rating")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    hospital = relationship("Hospital", back_populates="alerts")
    review = relationship("Review", back_populates="alerts")


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, unique=True)
    is_enabled = Column(Boolean, default=False)
    auto_reply_style = Column(String(20), default="empathy")  # empathy | guidance | apology
    hold_keywords = Column(Text, default="[]")  # JSON array
    require_approval = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    hospital = relationship("Hospital", back_populates="automation_rule")

    @property
    def hold_keyword_list(self):
        return json.loads(self.hold_keywords) if self.hold_keywords else []
