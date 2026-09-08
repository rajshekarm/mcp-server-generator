from clients.customer import CustomerApiClient


class CustomerService:
    def __init__(self, customer_client: CustomerApiClient) -> None:
        self.customer_client = customer_client

    async def get_customer(self, customer_id: str) -> dict:
        customer = await self.customer_client.get_customer(customer_id)

        return {
            "customer_id": customer["customerId"],
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer["phone"],
            "address": customer["address"],
        }
