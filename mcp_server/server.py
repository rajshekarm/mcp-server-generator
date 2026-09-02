from fastmcp import FastMCP

from mcp_server.clients.policy import PolicyApiClient
from mcp_server.mcp_util.tools.policy_tools import register_policy_tools
from mcp_server.services.policy_service import PolicyService


def create_server() -> FastMCP:
    mcp = FastMCP("insurance-mcp-server")

    policy_client = PolicyApiClient()
    policy_service = PolicyService(policy_client=policy_client)
    register_policy_tools(mcp=mcp, service=policy_service)

    return mcp


mcp = create_server()


if __name__ == "__main__":
    mcp.run()
