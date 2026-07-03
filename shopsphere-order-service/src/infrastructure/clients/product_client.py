import uuid
from typing import Any
import httpx
import jwt
from datetime import datetime, timedelta, timezone
from src.config import settings

class ProductClient:
    """Client for calling the Product Service APIs."""

    def __init__(self, base_url: str = settings.PRODUCT_SERVICE_URL, client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip('/')
        self._client = client

    def _get_client(self) -> httpx.AsyncClient:
        return self._client if self._client is not None else httpx.AsyncClient()

    def _generate_admin_token(self) -> str:
        """Generate an internal admin token to pass the Product Service RBAC checks."""
        payload = {
            "sub": "00000000-0000-0000-0000-000000000000",
            "role": "ADMIN",
            "type": "access",
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5)
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

    async def get_product(self, product_id: uuid.UUID) -> dict[str, Any] | None:
        """Retrieve details of a product from the Product Service."""
        client = self._get_client()
        try:
            # We don't need authentication for public GET products endpoint
            response = await client.get(f"{self.base_url}/api/v1/products/{product_id}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                return None
        except httpx.HTTPError:
            return None
        finally:
            if self._client is None:
                await client.aclose()

    async def deduct_stock(self, product_id: uuid.UUID, quantity: int) -> bool:
        """Reserve/deduct stock levels from the Product Service inventory."""
        client = self._get_client()
        token = self._generate_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/products/{product_id}/deduct",
                json={"quantity": quantity},
                headers=headers
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False
        finally:
            if self._client is None:
                await client.aclose()

    async def restock_stock(self, product_id: uuid.UUID, quantity: int) -> bool:
        """Add inventory back if an order is cancelled or checkout fails."""
        client = self._get_client()
        token = self._generate_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/products/{product_id}/restock",
                json={"quantity": quantity},
                headers=headers
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False
        finally:
            if self._client is None:
                await client.aclose()
