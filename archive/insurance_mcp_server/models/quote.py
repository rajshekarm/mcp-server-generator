from enum import StrEnum

from pydantic import BaseModel, Field


class QuoteStatus(StrEnum):
    DRAFT = "draft"
    REFERRED = "referred"
    APPROVED = "approved"
    DECLINED = "declined"


class Quote(BaseModel):
    id: str
    customer_id: str
    product: str
    risk_score: int = Field(ge=0, le=100)
    coverage_limit: float = Field(gt=0)
    annual_premium: float = Field(ge=0)
    status: QuoteStatus = QuoteStatus.DRAFT
