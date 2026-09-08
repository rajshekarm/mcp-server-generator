from archive.insurance_mcp_server.integrations.policy_admin import PolicyAdminClient
from archive.insurance_mcp_server.models.policy import Policy

class PolicyService:

    def __init__(
        self,
        policy_admin: PolicyAdminClient,
    ) -> None:
        self.policy_admin = policy_admin

    def get(
        self,
        policy_id: str,
    ) -> Policy | None:
        return self.policy_admin.get_policy(policy_id)

    def check_coverage(
        self,
        policy_id: str,
        loss_type: str,
    ) -> dict:

        policy = self.get(policy_id)

        if policy is None:
            return {
                "found": False,
                "covered": False,
                "policy_id": policy_id,
                "reason": "Policy not found",
            }

        if policy.status != "active":
            return {
                "found": True,
                "covered": False,
                "policy_id": policy_id,
                "reason": f"Policy is {policy.status}",
            }

        covered = loss_type in policy.coverages

        return {
            "found": True,
            "policy_id": policy_id,
            "loss_type": loss_type,
            "covered": covered,
            "reason": (
                "Coverage found"
                if covered
                else "Coverage not found"
            ),
        }