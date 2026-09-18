from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


PolicyStatus = Literal["active", "pending", "cancelled", "expired"]
ProductType = Literal["personal_auto", "homeowners"]

app = FastAPI(
    title="Insurance PolicyCenter API",
    description="Search policies, inspect coverage, and calculate endorsement quotes.",
    version="1.0.0",
)


class Coverage(BaseModel):
    code: str
    name: str
    limit: float
    deductible: float


class Policy(BaseModel):
    policy_number: str
    customer_id: str
    product: ProductType
    status: PolicyStatus
    effective_date: date
    expiration_date: date
    annual_premium: float
    coverages: list[Coverage]


class EndorsementQuoteRequest(BaseModel):
    change_type: Literal["increase_limit", "decrease_deductible", "add_driver"]
    coverage_code: str | None = None
    requested_value: float | None = Field(default=None, gt=0)


class EndorsementQuote(BaseModel):
    policy_number: str
    change_type: str
    current_annual_premium: float
    premium_change: float
    estimated_annual_premium: float


POLICIES: dict[str, Policy] = {
    "POL-1001": Policy(
        policy_number="POL-1001",
        customer_id="CUS-1001",
        product="personal_auto",
        status="active",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
        annual_premium=1200.00,
        coverages=[
            Coverage(code="BI", name="Bodily Injury Liability", limit=100000, deductible=0),
            Coverage(code="COLL", name="Collision", limit=50000, deductible=500),
        ],
    ),
    "POL-1002": Policy(
        policy_number="POL-1002",
        customer_id="CUS-1002",
        product="homeowners",
        status="active",
        effective_date=date(2026, 3, 1),
        expiration_date=date(2027, 2, 28),
        annual_premium=1800.00,
        coverages=[
            Coverage(code="DWELLING", name="Dwelling", limit=450000, deductible=2000),
            Coverage(
                code="PERSONAL_PROPERTY",
                name="Personal Property",
                limit=150000,
                deductible=2000,
            ),
        ],
    ),
}


def _find_policy(policy_number: str) -> Policy:
    policy = POLICIES.get(policy_number.upper())
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_number} was not found")
    return policy


@app.get("/health", operation_id="policy_center_health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/policies", response_model=list[Policy], operation_id="search_policies")
def search_policies(
    customer_id: str | None = Query(default=None),
    status: PolicyStatus | None = Query(default=None),
    product: ProductType | None = Query(default=None),
) -> list[Policy]:
    policies = list(POLICIES.values())
    if customer_id:
        policies = [p for p in policies if p.customer_id.upper() == customer_id.upper()]
    if status:
        policies = [p for p in policies if p.status == status]
    if product:
        policies = [p for p in policies if p.product == product]
    return policies


@app.get("/policies/{policy_number}", response_model=Policy, operation_id="get_policy")
def get_policy(policy_number: str) -> Policy:
    return _find_policy(policy_number)


@app.get(
    "/policies/{policy_number}/coverages",
    response_model=list[Coverage],
    operation_id="get_policy_coverages",
)
def get_policy_coverages(policy_number: str) -> list[Coverage]:
    return _find_policy(policy_number).coverages


@app.post(
    "/policies/{policy_number}/endorsement-quotes",
    response_model=EndorsementQuote,
    operation_id="calculate_endorsement_quote",
)
def calculate_endorsement_quote(
    policy_number: str,
    request: EndorsementQuoteRequest,
) -> EndorsementQuote:
    policy = _find_policy(policy_number)
    factors = {"increase_limit": 0.08, "decrease_deductible": 0.12, "add_driver": 0.18}
    change = round(policy.annual_premium * factors[request.change_type], 2)
    return EndorsementQuote(
        policy_number=policy.policy_number,
        change_type=request.change_type,
        current_annual_premium=policy.annual_premium,
        premium_change=change,
        estimated_annual_premium=round(policy.annual_premium + change, 2),
    )
