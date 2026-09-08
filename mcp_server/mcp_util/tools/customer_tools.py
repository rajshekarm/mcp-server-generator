from fastmcp import FastMCP

from services.customer_service import CustomerService


def register_customer_tools(
    mcp: FastMCP,
    service: CustomerService,
) -> None:
    @mcp.tool()
    async def get_customer(customer_id: str) -> dict:
        """Retrieve a customer by customer ID."""

        return await service.get_customer(customer_id)
