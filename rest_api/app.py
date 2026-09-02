from typing import Any

from fastapi import FastAPI, HTTPException


app = FastAPI(title="Policy REST API", version="1.0.0")


POLICIES: dict[str, dict[str, Any]] = {
    "POL-1001": {
        "policyNumber": "POL-1001",
        "policyStatus": "A",
        "effectiveDate": "2026-01-01",
        "expirationDate": "2026-12-31",
        "productName": "Auto Insurance",
        "annualPremium": 1200.00,
    },
    "POL-1002": {
        "policyNumber": "POL-1002",
        "policyStatus": "C",
        "effectiveDate": "2025-01-01",
        "expirationDate": "2025-12-31",
        "productName": "Home Insurance",
        "annualPremium": 1800.00,
    },
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/policies/{policy_number}")
async def get_policy(policy_number: str) -> dict[str, Any]:
    policy = POLICIES.get(policy_number.upper())

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail=f"Policy {policy_number} was not found",
        )

    return policy
