from urllib.parse import quote

from clients.base import BaseApiClient


class PolicyApiClient(BaseApiClient):

    async def get_policy(self, policy_number: str) -> dict:
        normalized_policy_number = policy_number.strip()

        if not normalized_policy_number:
            raise ValueError("Policy number cannot be empty")

        return await self.get(
            f"/policies/{quote(normalized_policy_number, safe='')}"
        )



