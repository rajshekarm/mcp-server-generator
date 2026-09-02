from typing import Any
import httpx

class BaseApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.json()
