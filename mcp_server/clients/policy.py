from mcp_server.clients.base import BaseApiClient


class PolicyApiClient(BaseApiClient):

    async def get_policy(self, policy_number: str) -> dict:

        return await self.get(
            f"/policies/{policy_number}"
        )



