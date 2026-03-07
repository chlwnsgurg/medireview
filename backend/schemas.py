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
    reply_content: Optional[str] = ""
    review_type: Optional[str] = None
    review_type_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Comment ───────────────────────────────────────────

class CommentBase(BaseModel):
    style: str
    content: str


STYLE_LABELS = {
    # 호감
    "pos_thanks": "감사 중심",
    "pos_highlight": "칭찬 강조",
    "pos_revisit": "재방문 유도",
    # 컴플레인
    "comp_empathy": "공감 중심",
    "comp_explain": "해명 중심",
    "comp_improve": "개선 약속",
    # 클레임
    "clm_apology": "사과 중심",
    "clm_cause": "원인 설명",
    "clm_prevent": "개선 대책",
    # 레거시 호환
    "empathy": "공감형",
    "guidance": "안내형",
    "apology": "사과형",
}


class CommentOut(CommentBase):
    id: int
    review_id: int
    style_label: str = ""
    is_selected: bool
    is_posted: bool
    created_at: datetime

    class Config:
        from_attributes = True

    def model_post_init(self, __context):
        if not self.style_label:
            self.style_label = STYLE_LABELS.get(self.style, self.style)


class CommentUpdateRequest(BaseModel):
    content: str


class CommentPostRequest(BaseModel):
    comment_id: int


class GenerateCommentsResponse(BaseModel):
    review_type: str
    review_type_reason: str
    comments: list[CommentOut]


class ReviewTypeUpdate(BaseModel):
    review_type: str


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
    auto_reply_positive_variant: str = "pos_thanks"
    auto_reply_complaint_variant: str = "comp_empathy"
    auto_reply_claim_variant: str = "clm_apology"
    hold_keywords: Optional[str] = "[]"
    require_approval: bool = False


class AutomationRuleUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    auto_reply_positive_variant: Optional[str] = None
    auto_reply_complaint_variant: Optional[str] = None
    auto_reply_claim_variant: Optional[str] = None
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
