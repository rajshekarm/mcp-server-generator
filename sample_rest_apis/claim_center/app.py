from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


ClaimStatus = Literal["reported", "investigating", "approved", "closed", "denied"]
LossType = Literal["collision", "theft", "property_damage", "water_damage"]

app = FastAPI(
    title="Insurance ClaimCenter API",
    description="Report, search, and manage insurance claims.",
    version="1.0.0",
)


class Claim(BaseModel):
    claim_number: str
    policy_number: str
    customer_id: str
    loss_date: date
    loss_type: LossType
    description: str
    status: ClaimStatus
    reserve_amount: float
    paid_amount: float


class ReportClaimRequest(BaseModel):
    policy_number: str = Field(min_length=3, max_length=30)
    customer_id: str = Field(min_length=3, max_length=30)
    loss_date: date
    loss_type: LossType
    description: str = Field(min_length=10, max_length=2000)
    estimated_loss: float = Field(gt=0, le=10_000_000)


class UpdateClaimStatusRequest(BaseModel):
    status: ClaimStatus
    note: str = Field(min_length=3, max_length=500)


CLAIMS: dict[str, Claim] = {
    "CLM-1001": Claim(
        claim_number="CLM-1001",
        policy_number="POL-1001",
        customer_id="CUS-1001",
        loss_date=date(2026, 8, 20),
        loss_type="collision",
        description="Rear-end collision at a traffic signal.",
        status="investigating",
        reserve_amount=8500,
        paid_amount=1200,
    ),
    "CLM-1002": Claim(
        claim_number="CLM-1002",
        policy_number="POL-1002",
        customer_id="CUS-1002",
        loss_date=date(2026, 7, 14),
        loss_type="water_damage",
        description="Kitchen damage caused by a leaking supply pipe.",
        status="approved",
        reserve_amount=15000,
        paid_amount=5000,
    ),
}


def _find_claim(claim_number: str) -> Claim:
    claim = CLAIMS.get(claim_number.upper())
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_number} was not found")
    return claim


@app.get("/health", operation_id="claim_center_health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/claims", response_model=list[Claim], operation_id="search_claims")
def search_claims(
    policy_number: str | None = Query(default=None),
    customer_id: str | None = Query(default=None),
    status: ClaimStatus | None = Query(default=None),
) -> list[Claim]:
    claims = list(CLAIMS.values())
    if policy_number:
        claims = [c for c in claims if c.policy_number.upper() == policy_number.upper()]
    if customer_id:
        claims = [c for c in claims if c.customer_id.upper() == customer_id.upper()]
    if status:
        claims = [c for c in claims if c.status == status]
    return claims


@app.get("/claims/{claim_number}", response_model=Claim, operation_id="get_claim")
def get_claim(claim_number: str) -> Claim:
    return _find_claim(claim_number)


@app.post("/claims", response_model=Claim, status_code=201, operation_id="report_claim")
def report_claim(request: ReportClaimRequest) -> Claim:
    next_number = max(int(number.split("-")[1]) for number in CLAIMS) + 1
    claim_number = f"CLM-{next_number}"
    claim = Claim(
        claim_number=claim_number,
        policy_number=request.policy_number.upper(),
        customer_id=request.customer_id.upper(),
        loss_date=request.loss_date,
        loss_type=request.loss_type,
        description=request.description,
        status="reported",
        reserve_amount=request.estimated_loss,
        paid_amount=0,
    )
    CLAIMS[claim_number] = claim
    return claim


@app.patch(
    "/claims/{claim_number}/status",
    response_model=Claim,
    operation_id="update_claim_status",
)
def update_claim_status(
    claim_number: str,
    request: UpdateClaimStatusRequest,
) -> Claim:
    claim = _find_claim(claim_number)
    claim.status = request.status
    return claim
