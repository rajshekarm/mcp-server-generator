from typing import Any

from fastapi import FastAPI, HTTPException


app = FastAPI(title="Insurance REST API", version="1.0.0")


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

CUSTOMERS: dict[str, dict[str, Any]] = {
    "CUS-1001": {
        "customerId": "CUS-1001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0101",
        "address": "100 Main Street, Chicago, IL",
    },
    "CUS-1002": {
        "customerId": "CUS-1002",
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+1-555-0102",
        "address": "200 Oak Avenue, Austin, TX",
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


@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str) -> dict[str, Any]:
    customer = CUSTOMERS.get(customer_id.upper())

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} was not found",
        )

    return customer
