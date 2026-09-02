from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class PolicyStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"



class Policy(BaseModel):
    policy_id: str
    customer_name: str
    status: str
    product: str
    coverages: list[str]