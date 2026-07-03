import pytest
from src.domain.models import ProductStatus

@pytest.mark.asyncio
async def test_category_rbac_and_crud(client, admin_headers, customer_headers):
    # 1. Customer attempts to create category (Expected: 403 Forbidden)
    category_payload = {"name": "Video Games", "description": "Console games"}
    cust_res = await client.post("/api/v1/categories/", json=category_payload, headers=customer_headers)
    assert cust_res.status_code == 403

    # 2. Admin attempts to create category (Expected: 201 Created)
    admin_res = await client.post("/api/v1/categories/", json=category_payload, headers=admin_headers)
    assert admin_res.status_code == 201
    category_data = admin_res.json()
    assert category_data["name"] == "Video Games"
    assert category_data["slug"] == "video-games"
    category_id = category_data["id"]

    # 3. Public lists categories (Expected: 200 OK)
    list_res = await client.get("/api/v1/categories/")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Admin updates category (Expected: 200 OK)
    update_payload = {"name": "Gaming Consoles & Games"}
    update_res = await client.put(f"/api/v1/categories/{category_id}", json=update_payload, headers=admin_headers)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Gaming Consoles & Games"
    assert update_res.json()["slug"] == "gaming-consoles-games"

    # 5. Admin deletes category (Expected: 204 No Content)
    del_res = await client.delete(f"/api/v1/categories/{category_id}", headers=admin_headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_product_rbac_and_catalog_operations(client, admin_headers, customer_headers):
    # Create Category for Product test
    category_res = await client.post(
        "/api/v1/categories/",
        json={"name": "Computers"},
        headers=admin_headers
    )
    category_id = category_res.json()["id"]

    # 1. Customer attempts to create product (Expected: 403 Forbidden)
    product_payload = {
        "name": "MacBook Pro M3",
        "price": 1999.99,
        "inventory_quantity": 20,
        "description": "Apple Silicon Laptop",
        "category_id": category_id
    }
    cust_product_res = await client.post("/api/v1/products/", json=product_payload, headers=customer_headers)
    assert cust_product_res.status_code == 403

    # 2. Admin creates product (Expected: 201 Created)
    admin_product_res = await client.post("/api/v1/products/", json=product_payload, headers=admin_headers)
    assert admin_product_res.status_code == 201
    product_data = admin_product_res.json()
    product_id = product_data["id"]
    assert product_data["name"] == "MacBook Pro M3"
    assert product_data["slug"] == "macbook-pro-m3"
    assert product_data["inventory_quantity"] == 20

    # 3. Public queries product catalog with filters (Expected: 200 OK)
    get_res = await client.get(
        f"/api/v1/products/?search=MacBook&category_id={category_id}&min_price=1000.00&sort_by=price&sort_order=desc"
    )
    assert get_res.status_code == 200
    catalog = get_res.json()
    assert catalog["total_count"] == 1
    assert catalog["products"][0]["id"] == product_id

    # 4. Admin deducts stock level (Expected: 200 OK)
    deduct_res = await client.post(
        f"/api/v1/products/{product_id}/deduct",
        json={"quantity": 5},
        headers=admin_headers
    )
    assert deduct_res.status_code == 200
    assert deduct_res.json()["inventory_quantity"] == 15

    # 5. Customer attempts to delete product (Expected: 403 Forbidden)
    cust_del_res = await client.delete(f"/api/v1/products/{product_id}", headers=customer_headers)
    assert cust_del_res.status_code == 403

    # 6. Admin deletes product (Expected: 204 No Content)
    admin_del_res = await client.delete(f"/api/v1/products/{product_id}", headers=admin_headers)
    assert admin_del_res.status_code == 204
