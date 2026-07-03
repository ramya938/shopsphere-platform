import pytest
import uuid
from src.domain.models import OrderStatus

@pytest.mark.asyncio
async def test_place_direct_order_api(client, customer_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Keyboard", 79.99, 15)

    payload = {
        "items": [
            {"product_id": str(product_id), "quantity": 2}
        ],
        "shipping_address": "123 Main Street"
    }

    response = await client.post("/api/v1/orders/", json=payload, headers=customer_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == OrderStatus.CREATED
    assert data["total_price"] == 159.98
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == str(product_id)
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_checkout_cart_api(client, customer_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Keyboard", 79.99, 15)

    # 1. Add item to cart
    await client.post("/api/v1/cart/items", json={"product_id": str(product_id), "quantity": 3}, headers=customer_headers)

    # 2. Checkout cart
    payload = {
        "shipping_address": "456 Oak Avenue"
    }
    response = await client.post("/api/v1/orders/checkout", json=payload, headers=customer_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == OrderStatus.CREATED
    assert data["total_price"] == 239.97
    assert data["items"][0]["product_id"] == str(product_id)
    assert data["items"][0]["quantity"] == 3

    # 3. Check cart is now empty
    cart_response = await client.get("/api/v1/cart/", headers=customer_headers)
    assert len(cart_response.json()["items"]) == 0


@pytest.mark.asyncio
async def test_list_my_orders_api(client, customer_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Keyboard", 79.99, 15)

    # Place an order
    await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": str(product_id), "quantity": 1}], "shipping_address": "Addr"},
        headers=customer_headers
    )

    response = await client.get("/api/v1/orders/me", headers=customer_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_list_all_orders_rbac(client, customer_headers, admin_headers):
    # Customer gets 403 Forbidden
    response = await client.get("/api/v1/orders/", headers=customer_headers)
    assert response.status_code == 403

    # Admin gets 200 OK
    response = await client.get("/api/v1/orders/", headers=admin_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_order_status_workflow(client, customer_headers, admin_headers, mock_product_client):
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Keyboard", 79.99, 15)

    # 1. Place order
    res = await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": str(product_id), "quantity": 1}], "shipping_address": "Addr"},
        headers=customer_headers
    )
    order_id = res.json()["id"]

    # 2. Try to transition to invalid status (e.g., CREATED to SHIPPED immediately)
    response = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": OrderStatus.SHIPPED},
        headers=admin_headers
    )
    assert response.status_code == 400

    # 3. Transition to PAID (Allowed)
    response = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": OrderStatus.PAID},
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == OrderStatus.PAID

    # 4. Customer cancels order (Allowed from PAID stage)
    response = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": OrderStatus.CANCELLED},
        headers=customer_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == OrderStatus.CANCELLED
