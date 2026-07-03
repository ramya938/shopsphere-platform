import asyncio
import os
import sys

# Force in-memory SQLite database for the simulation run
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"
os.environ["LOG_LEVEL"] = "WARNING"

# Resolve absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
USER_SERVICE_PATH = os.path.join(BASE_DIR, "shopsphere-user-service")
PRODUCT_SERVICE_PATH = os.path.join(BASE_DIR, "shopsphere-product-service")

# --- Step 1: Import User Service components ---
sys.path.insert(0, USER_SERVICE_PATH)
from src.main import app as user_app
from src.domain.models import Base as UserBase
from src.infrastructure.database import engine as user_engine
sys.path.pop(0)

# Clean sys.modules cache to prevent import collisions on 'src'
for key in list(sys.modules.keys()):
    if key == "src" or key.startswith("src."):
        del sys.modules[key]

# --- Step 2: Import Product Service components ---
sys.path.insert(0, PRODUCT_SERVICE_PATH)
from src.main import app as product_app
from src.domain.models import Base as ProductBase
from src.infrastructure.database import engine as product_engine
sys.path.pop(0)

from httpx import AsyncClient, ASGITransport
import jwt
from datetime import datetime, timedelta, timezone

async def init_databases():
    # Setup sqlite memory tables
    async with user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
    async with product_engine.begin() as conn:
        await conn.run_sync(ProductBase.metadata.create_all)
    print("✅ Databases initialized in memory successfully.")

async def run_simulation():
    print("\n--- Starting ShopSphere AI Microservices Simulation ---\n")
    
    # HTTP Async clients mapping to ASGI apps
    user_client = AsyncClient(transport=ASGITransport(app=user_app), base_url="http://user-service")
    product_client = AsyncClient(transport=ASGITransport(app=product_app), base_url="http://product-service")

    # 1. Register Customer on User Service
    print("1. [Customer Registration] Registering a new customer account...")
    reg_payload = {
        "email": "jane.doe@shopsphere.ai",
        "password": "SecurePassword123",
        "full_name": "Jane Doe",
        "role": "CUSTOMER"
    }
    res = await user_client.post("/api/v1/auth/register", json=reg_payload)
    print(f"   Response Status: {res.status_code}")
    print(f"   Response Body: {res.json()}\n")
    
    # 2. Login Customer to retrieve token
    print("2. [Customer Authentication] Authenticating Jane Doe...")
    login_payload = {
        "email": "jane.doe@shopsphere.ai",
        "password": "SecurePassword123"
    }
    res = await user_client.post("/api/v1/auth/login", json=login_payload)
    print(f"   Response Status: {res.status_code}")
    token_data = res.json()
    print(f"   Access Token: {token_data['access_token'][:40]}...")
    customer_token = token_data["access_token"]
    print(f"   Refresh Token: {token_data['refresh_token'][:40]}...\n")

    # 3. Register Admin on User Service
    print("3. [Admin Registration] Registering an administrator account...")
    admin_payload = {
        "email": "admin@shopsphere.ai",
        "password": "AdminPassword123",
        "full_name": "System Administrator",
        "role": "ADMIN"
    }
    res = await user_client.post("/api/v1/auth/register", json=admin_payload)
    print(f"   Response Status: {res.status_code}\n")

    # 4. Login Admin to retrieve token
    print("4. [Admin Authentication] Authenticating Administrator...")
    res = await user_client.post("/api/v1/auth/login", json={"email": "admin@shopsphere.ai", "password": "AdminPassword123"})
    admin_token = res.json()["access_token"]
    print(f"   Admin Token: {admin_token[:40]}...\n")

    # 5. Admin creates Category on Product Service
    print("5. [Category Creation] Admin creating a category on Product Service...")
    cat_payload = {"name": "Electronics", "description": "Phones, laptops, and gadgets"}
    res = await product_client.post(
        "/api/v1/categories/", 
        json=cat_payload, 
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"   Response Status: {res.status_code}")
    category = res.json()
    print(f"   Category JSON: {category}\n")
    category_id = category["id"]

    # 6. Admin creates Product inside Category
    print("6. [Product Creation] Admin listing a new product on Product Service...")
    prod_payload = {
        "name": "iPhone 15 Pro Max",
        "description": "Latest Apple smartphone with titanium frame.",
        "price": 1199.99,
        "inventory_quantity": 5,
        "image_url": "https://example.com/iphone15.jpg",
        "status": "ACTIVE",
        "category_id": category_id
    }
    res = await product_client.post(
        "/api/v1/products/", 
        json=prod_payload, 
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"   Response Status: {res.status_code}")
    product = res.json()
    print(f"   Product JSON: {product}\n")
    product_id = product["id"]

    # 7. Customer searches for "iPhone" in Product Service
    print("7. [Product Search] Customer searching for 'iPhone'...")
    res = await product_client.get("/api/v1/products/?search=iPhone&limit=5")
    print(f"   Response Status: {res.status_code}")
    search_results = res.json()
    print(f"   Total found: {search_results['total_count']}")
    print(f"   First Product: {search_results['products'][0]['name']} (Price: ${search_results['products'][0]['price']}, Stock: {search_results['products'][0]['inventory_quantity']})\n")

    # 8. Customer attempts to access list_all users (Forbidden RBAC check)
    print("8. [RBAC Check: Forbidden] Customer attempts to list all users from User Service...")
    res = await user_client.get("/api/v1/users/", headers={"Authorization": f"Bearer {customer_token}"})
    print(f"   Response Status: {res.status_code}")
    print(f"   Response Detail: {res.json()}\n")

    # 9. Admin lists all users (Allowed RBAC check)
    print("9. [RBAC Check: Allowed] Admin lists all users from User Service...")
    res = await user_client.get("/api/v1/users/", headers={"Authorization": f"Bearer {admin_token}"})
    print(f"   Response Status: {res.status_code}")
    users = res.json()
    print(f"   Users found: {len(users)}")
    print(f"   List: {[u['email'] for u in users]}\n")

    # 10. Admin deducts Product Stock (Checkout reservation simulation)
    print("10. [Inventory Transaction] Admin deducting 2 iPhones from Product Service...")
    res = await product_client.post(
        f"/api/v1/products/{product_id}/deduct",
        json={"quantity": 2},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"   Response Status: {res.status_code}")
    updated_product = res.json()
    print(f"   New stock level: {updated_product['inventory_quantity']} (Status: {updated_product['status']})\n")

    print("--- Simulation Ended Successfully. Both microservices coordinate and authorize statelessly. ---")

async def main():
    await init_databases()
    await run_simulation()

if __name__ == "__main__":
    asyncio.run(main())
