from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
