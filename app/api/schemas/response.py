from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    daily_quota: int = 5
    today_usage: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class JobCreateResponse(BaseModel):
    job_id: str
    phase: str
    created_at: datetime


class JobStatusResponse(BaseModel):
    job_id: str
    phase: str
    progress_percent: int
    current_step_detail: str
    is_cancelled: bool
    requires_human_approval: bool
    human_approved: bool | None
    total_cost_usd: float
    cost_budget_usd: float
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    download_url: str | None = None
    script_preview_url: str | None = None

    model_config = {"from_attributes": True}


class JobStepResponse(BaseModel):
    step_name: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_sec: float | None = None
    cost_usd: float = 0.0
    error_message: str | None = None

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    has_next: bool
