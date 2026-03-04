from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Hospital ──────────────────────────────────────────

class HospitalBase(BaseModel):
    name: str
    naver_place_id: str = ""
    tone_style: str = "polite"
    alert_threshold: int = 2


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    naver_place_id: Optional[str] = None
    tone_style: Optional[str] = None
    alert_threshold: Optional[int] = None


class HospitalOut(HospitalBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Review ────────────────────────────────────────────

class ReviewBase(BaseModel):
    platform: str
    platform_review_id: Optional[str] = None
    author: Optional[str] = None
    rating: float
    rating_scale: int = 5
    content: Optional[str] = None
    image_urls: Optional[str] = "[]"
    reviewed_at: Optional[datetime] = None


class ReviewOut(ReviewBase):
    id: int
    hospital_id: int
    is_replied: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Comment ───────────────────────────────────────────

class CommentBase(BaseModel):
    style: str
    content: str


class CommentOut(CommentBase):
    id: int
    review_id: int
    is_selected: bool
    is_posted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CommentPostRequest(BaseModel):
    comment_id: int


# ── Alert ─────────────────────────────────────────────

class AlertOut(BaseModel):
    id: int
    hospital_id: int
    review_id: int
    comment_id: Optional[int] = None
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── AutomationRule ────────────────────────────────────

class AutomationRuleBase(BaseModel):
    is_enabled: bool = False
    auto_reply_style: str = "empathy"
    hold_keywords: Optional[str] = "[]"
    require_approval: bool = False


class AutomationRuleUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    auto_reply_style: Optional[str] = None
    hold_keywords: Optional[str] = None
    require_approval: Optional[bool] = None


class AutomationRuleOut(AutomationRuleBase):
    id: int
    hospital_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── 리뷰 통계 ────────────────────────────────────────

class ReviewStats(BaseModel):
    total_count: int
    average_rating: float
    unreplied_count: int
    platform_stats: list  # [{ "platform": "naver", "count": 10, "avg_rating": 4.2 }]
    rating_distribution: dict  # { "1": 5, "2": 8, ... }


class PaginatedReviews(BaseModel):
    total: int
    page: int
    size: int
    items: list[ReviewOut]


# ── AutomationLog ─────────────────────────────────────

class AutomationLogOut(BaseModel):
    id: int
    hospital_id: int
    review_id: int
    comment_id: Optional[int] = None
    action: str
    status: str
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
