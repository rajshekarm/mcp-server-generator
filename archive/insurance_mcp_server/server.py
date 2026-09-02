from fastmcp import FastMCP

from integrations.policy_admin import PolicyAdminClient
from services.policy_service import PolicyService
from tools.policy import register_policy_tools


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