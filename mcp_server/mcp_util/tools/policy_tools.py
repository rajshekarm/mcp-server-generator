from fastmcp import FastMCP

from services.policy_service import PolicyService

def register_policy_tools(
    mcp: FastMCP,
    service: PolicyService,
) -> None:

    @mcp.tool()
    async def get_policy(policy_number: str) -> dict:
        """Retrieve an insurance policy by policy number."""

        return await service.get_policy(policy_number)
