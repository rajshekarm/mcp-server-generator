# services/insurance_summary.py

class InsuranceSummaryService:

    def __init__(
        self,
        customer_client,
        policy_client,
        claims_client,
    ):
        self.customer_client = customer_client
        self.policy_client = policy_client
        self.claims_client = claims_client

    async def get_summary(
        self,
        customer_id: str,
    ) -> dict:

        customer = await self.customer_client.get_customer(
            customer_id
        )

        policies = await self.policy_client.get_customer_policies(
            customer_id
        )

        claims = await self.claims_client.get_customer_claims(
            customer_id
        )

        return {
            "customer": {
                "customer_id": customer["customerId"],
                "name": customer["name"],
            },
            "policies": policies,
            "claims": claims,
        }