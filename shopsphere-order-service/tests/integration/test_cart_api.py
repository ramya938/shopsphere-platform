import pytest
import uuid

@pytest.mark.asyncio
async def test_get_cart_unauthorized(client):
    response = await client.get("/api/v1/cart/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_cart_authorized(client, customer_headers):
    response = await client.get("/api/v1/cart/", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_add_item_to_cart(client, customer_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Monitor", 299.99, 5)

    payload = {
        "product_id": str(product_id),
        "quantity": 2
    }
    response = await client.post("/api/v1/cart/items", json=payload, headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == str(product_id)
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_add_item_to_cart_insufficient_stock(client, customer_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Monitor", 299.99, 1)

    payload = {
        "product_id": str(product_id),
        "quantity": 5
    }
    response = await client.post("/api/v1/cart/items", json=payload, headers=customer_headers)
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"] or "stock" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_cart_item(client, customer_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Monitor", 299.99, 10)

    # Add item
    await client.post("/api/v1/cart/items", json={"product_id": str(product_id), "quantity": 2}, headers=customer_headers)

    # Update item quantity
    payload = {"quantity": 4}
    response = await client.put(f"/api/v1/cart/items/{product_id}", json=payload, headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["quantity"] == 4


@pytest.mark.asyncio
async def test_remove_cart_item(client, customer_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Monitor", 299.99, 10)

    # Add item
    await client.post("/api/v1/cart/items", json={"product_id": str(product_id), "quantity": 2}, headers=customer_headers)

    # Remove item
    response = await client.delete(f"/api/v1/cart/items/{product_id}", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
