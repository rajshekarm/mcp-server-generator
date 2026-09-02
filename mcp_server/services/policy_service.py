from mcp_server.clients.policy import PolicyApiClient


class PolicyService:

    def __init__(self, policy_client: PolicyApiClient,
    ):
        self.policy_client = policy_client


    async def get_policy(
        self,
        policy_number: str,
    ) -> dict:

        policy = await self.policy_client.get_policy(
            policy_number
        )

        return {
            "policy_number": policy["policyNumber"],
            "status": self._map_status(
                policy["policyStatus"]
            ),
            "effective_date": policy["effectiveDate"],
            "expiration_date": policy["expirationDate"],
            "product": policy["productName"],
            "premium": policy["annualPremium"],
        }


    # async def search_policies(
    #     self,
    #     customer_id: str | None = None,
    #     policy_number: str | None = None,
    #     status: str | None = None,
    # ) -> dict:

    #     if not any([
    #         customer_id,
    #         policy_number,
    #         status,
    #     ]):
    #         raise ValueError(
    #             "At least one search parameter is required."
    #         )

    #     policies = await self.policy_client.search_policies(
    #         customer_id=customer_id,
    #         policy_number=policy_number,
    #         status=status,
    #     )

    #     return {
    #         "count": len(policies),
    #         "policies": [
    #             {
    #                 "policy_number": p["policyNumber"],
    #                 "status": self._map_status(
    #                     p["policyStatus"]
    #                 ),
    #                 "product": p["productName"],
    #             }
    #             for p in policies
    #         ],
    #     }


    # async def get_policy_coverage(
    #     self,
    #     policy_number: str,
    # ) -> dict:

    #     coverages = (
    #         await self.policy_client.get_policy_coverage(
    #             policy_number
    #         )
    #     )

    #     return {
    #         "policy_number": policy_number,
    #         "coverages": coverages,
    #     }


    # async def get_policy_documents(
    #     self,
    #     policy_number: str,
    # ) -> dict:

    #     documents = (
    #         await self.policy_client.get_policy_documents(
    #             policy_number
    #         )
    #     )

    #     return {
    #         "policy_number": policy_number,
    #         "documents": documents,
    #     }


    # async def get_payment_summary(
    #     self,
    #     policy_number: str,
    # ) -> dict:

    #     billing = (
    #         await self.policy_client.get_payment_summary(
    #             policy_number
    #         )
    #     )

    #     return {
    #         "policy_number": policy_number,
    #         "balance": billing["balance"],
    #         "next_payment_date": billing[
    #             "nextPaymentDate"
    #         ],
    #         "payment_status": billing["status"],
    #     }


    @staticmethod
    def _map_status(status: str) -> str:

        mapping = {
            "A": "ACTIVE",
            "C": "CANCELLED",
            "E": "EXPIRED",
            "P": "PENDING",
        }

        return mapping.get(
            status,
            "UNKNOWN"
        )
