from fastmcp import FastMCP

from services.policy_service import PolicyService


def register_policy_tools(
    mcp: FastMCP,
    service: PolicyService,
) -> None:

    @mcp.tool
    def get_policy(policy_id: str) -> dict:
        """
        Get policy details by policy ID.
        """

        policy = service.get(policy_id)

        if policy is None:
            return {
                "found": False,
                "policy_id": policy_id,
                "message": "Policy not found",
            }

        return {
            "found": True,
            "policy": policy.model_dump(mode="json"),
        }


    @mcp.tool
    def check_policy_status(policy_id: str) -> dict:
        """
        Check whether a policy is active, inactive,
        cancelled, or expired.
        """

        policy = service.get(policy_id)

        if policy is None:
            return {
                "found": False,
                "policy_id": policy_id,
                "message": "Policy not found",
            }

        return {
            "found": True,
            "policy_id": policy.policy_id,
            "status": policy.status,
        }


    @mcp.tool
    def check_coverage(
        policy_id: str,
        loss_type: str,
    ) -> dict:
        """
        Check whether a policy includes coverage
        for a given loss type.
        """

        return service.check_coverage(
            policy_id=policy_id,
            loss_type=loss_type,
        )