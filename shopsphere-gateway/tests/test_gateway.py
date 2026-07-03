import jwt
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from httpx import AsyncClient
from pytest_httpx import HTTPXMock
import fakeredis.aioredis

from src.config import settings
from src.core.redis import redis_manager

def generate_test_token(user_id: str, role: str, expired: bool = False) -> str:
    delta = timedelta(minutes=-15) if expired else timedelta(minutes=15)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + delta
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.mark.asyncio
async def test_gateway_health_check(client: AsyncClient, httpx_mock: HTTPXMock):
    # Mock health endpoints of child services
    httpx_mock.add_response(url="http://user-service:8000/health", json={"status": "healthy"})
    httpx_mock.add_response(url="http://product-service:8001/health", json={"status": "healthy"})
    httpx_mock.add_response(url="http://order-service:8002/health", json={"status": "healthy"})

    response = await client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dependencies"]["redis"] == "healthy"
    assert data["dependencies"]["user_service"] == "healthy"


@pytest.mark.asyncio
async def test_gateway_routing_post_login(client: AsyncClient, httpx_mock: HTTPXMock):
    # Mock downstream login endpoint
    mock_payload = {"access_token": "token123", "token_type": "bearer"}
    httpx_mock.add_response(
        method="POST",
        url="http://user-service:8000/api/v1/auth/login",
        json=mock_payload,
        status_code=200
    )

    response = await client.post("/api/v1/auth/login", json={"email": "test@test.com", "password": "password"})
    assert response.status_code == 200
    assert response.json() == mock_payload


@pytest.mark.asyncio
async def test_gateway_unmatched_route_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/unknown")
    assert response.status_code == 404
    assert "Route not found in API Gateway" in response.json()["detail"]


@pytest.mark.asyncio
async def test_gateway_valid_jwt_validation_and_forwarding(client: AsyncClient, httpx_mock: HTTPXMock):
    user_id = str(uuid.uuid4())
    token = generate_test_token(user_id, "CUSTOMER")

    # Verify downstream receives injected headers
    def request_callback(request):
        import httpx
        assert request.headers.get("X-User-Id") == user_id
        assert request.headers.get("X-User-Role") == "CUSTOMER"
        return httpx.Response(status_code=200, json={"items": []})

    httpx_mock.add_callback(
        request_callback,
        method="GET",
        url="http://order-service:8002/api/v1/cart"
    )

    response = await client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_gateway_expired_jwt_returns_401(client: AsyncClient):
    token = generate_test_token(str(uuid.uuid4()), "CUSTOMER", expired=True)
    response = await client.get("/api/v1/cart", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


@pytest.mark.asyncio
async def test_gateway_invalid_jwt_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/cart", headers={"Authorization": "Bearer invalid_signature_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_gateway_caching_behavior(client: AsyncClient, httpx_mock: HTTPXMock, mock_redis_connection):
    # Clear cache in fakeredis
    await mock_redis_connection.flushall()

    # Call 1: Miss, fetch downstream
    httpx_mock.add_response(
        method="GET",
        url="http://product-service:8001/api/v1/products?limit=10",
        json={"products": [{"id": 1, "name": "Laptop"}]},
        status_code=200
    )

    r1 = await client.get("/api/v1/products?limit=10")
    assert r1.status_code == 200
    assert r1.headers.get("X-Cache") is None

    # Call 2: Hit, should return from cache directly (no HTTPXMock setup necessary)
    r2 = await client.get("/api/v1/products?limit=10")
    assert r2.status_code == 200
    assert r2.headers.get("X-Cache") == "HIT"
    assert r2.json()["products"][0]["name"] == "Laptop"


@pytest.mark.asyncio
async def test_gateway_rate_limiting(client: AsyncClient, httpx_mock: HTTPXMock, mock_redis_connection):
    await mock_redis_connection.flushall()
    
    # Configure low limit for rate testing
    with patch.object(settings, "RATE_LIMIT_ANON", 2):
        # We make 3 requests. 2 should be allowed, 3rd blocked.
        httpx_mock.add_response(
            method="GET",
            url="http://product-service:8001/api/v1/products",
            json={"products": []},
            status_code=200
        )

        # 1st request
        r1 = await client.get("/api/v1/products")
        assert r1.status_code == 200

        # 2nd request
        r2 = await client.get("/api/v1/products")
        assert r2.status_code == 200

        # 3rd request
        r3 = await client.get("/api/v1/products")
        assert r3.status_code == 429
        assert "Rate limit exceeded" in r3.json()["detail"]
