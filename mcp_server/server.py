import os

from fastmcp import FastMCP

from mcp_util.tools.policy_tools import register_policy_tools
from services.policy_service import PolicyService
from clients.policy import PolicyApiClient

# from mcp_util.tools.claims_tools import register_claim_tools
# from mcp_util.tools.customer_tools import register_customer_tools


mcp = FastMCP("insurance-mcp-server")
policy_client = PolicyApiClient(
    base_url=os.getenv(
        "POLICY_API_BASE_URL",
        "http://127.0.0.1:8000",
    )
)

policy_service = PolicyService(
    policy_client=policy_client
)


register_policy_tools(
    mcp=mcp,
    service=policy_service,
)

# register_claim_tools(mcp)
# register_customer_tools(mcp)


if __name__ == "__main__":
    mcp.run()
