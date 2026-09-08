from fastmcp import FastMCP

from archive.insurance_mcp_server.integrations.policy_admin import PolicyAdminClient
from archive.insurance_mcp_server.services.policy_service import PolicyService
from archive.insurance_mcp_server.tools.policy import register_policy_tools


def create_server() -> FastMCP:
    mcp = FastMCP("Insurance MCP")

    policy_admin = PolicyAdminClient()

    policy_service = PolicyService(
        policy_admin=policy_admin
    )

    register_policy_tools(
        mcp=mcp,
        service=policy_service,
    )

    return mcp

mcp = create_server()

if __name__ == "__main__":
    mcp.run()