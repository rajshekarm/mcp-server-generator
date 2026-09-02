from typing import Any


class BaseApiClient:

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "policyNumber": "POL-1001",
            "policyStatus": "A",
            "effectiveDate": "2026-01-01",
            "expirationDate": "2026-12-31",
            "productName": "Auto Insurance",
            "annualPremium": 1200.00,
        }

    async def post(self, path, **kwargs):
        ...

    async def put(self, path, **kwargs):
        ...

    async def delete(self, path, **kwargs):
        ...
