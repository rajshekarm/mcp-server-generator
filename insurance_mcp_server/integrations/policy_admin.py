from models.policy import Policy


class PolicyAdminClient:

    def __init__(self) -> None:
        self.policies = {
            "POL-1001": Policy(
                policy_id="POL-1001",
                customer_name="John Doe",
                status="active",
                product="auto",
                coverages=[
                    "collision",
                    "theft",
                    "liability",
                ],
            ),
            "POL-1002": Policy(
                policy_id="POL-1002",
                customer_name="Jane Smith",
                status="expired",
                product="home",
                coverages=[
                    "fire",
                    "water",
                ],
            ),
        }

    def get_policy(
        self,
        policy_id: str,
    ) -> Policy | None:
        return self.policies.get(policy_id)