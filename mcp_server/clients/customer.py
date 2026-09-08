from urllib.parse import quote

from clients.base import BaseApiClient


class CustomerApiClient(BaseApiClient):
    async def get_customer(self, customer_id: str) -> dict:
        normalized_customer_id = customer_id.strip()

        if not normalized_customer_id:
            raise ValueError("Customer ID cannot be empty")

        return await self.get(
            f"/customers/{quote(normalized_customer_id, safe='')}"
        )
