import pytest

@pytest.mark.asyncio
async def test_auth_and_profile_flow(client):
    """
    Test user registration, login, profile retrieval, profile updates, 
    refresh token rotation, and account deletion.
    """
    # 1. Register User (CUSTOMER role)
    register_payload = {
        "email": "customer_api@shopsphere.ai",
        "password": "customerSecretPassword123",
        "full_name": "API Customer",
        "role": "CUSTOMER"
    }
    register_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_res.status_code == 201
    user_data = register_res.json()
    assert user_data["email"] == "customer_api@shopsphere.ai"
    assert user_data["role"] == "CUSTOMER"
    assert "id" in user_data
    
    # 2. Login User
    login_payload = {
        "email": "customer_api@shopsphere.ai",
        "password": "customerSecretPassword123"
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 3. Retrieve Profile
    profile_res = await client.get("/api/v1/users/me", headers=headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["email"] == "customer_api@shopsphere.ai"
    assert profile_res.json()["full_name"] == "API Customer"
    
    # 4. Update Profile
    update_payload = {
        "full_name": "Updated API Customer",
        "email": "customer_api_new@shopsphere.ai"
    }
    update_res = await client.put("/api/v1/users/me", headers=headers, json=update_payload)
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Updated API Customer"
    assert update_res.json()["email"] == "customer_api_new@shopsphere.ai"
    
    # 5. Rotate Refresh Token
    refresh_payload = {
        "refresh_token": refresh_token
    }
    refresh_res = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert refresh_res.status_code == 200
    rotated_token_data = refresh_res.json()
    assert "access_token" in rotated_token_data
    assert "refresh_token" in rotated_token_data
    
    new_access_token = rotated_token_data["access_token"]
    new_headers = {"Authorization": f"Bearer {new_access_token}"}
    
    # 6. Verify profile works with the new access token
    new_profile_res = await client.get("/api/v1/users/me", headers=new_headers)
    assert new_profile_res.status_code == 200
    assert new_profile_res.json()["email"] == "customer_api_new@shopsphere.ai"
    
    # 7. Delete Account
    delete_res = await client.delete("/api/v1/users/me", headers=new_headers)
    assert delete_res.status_code == 204
    
    # Verify profile retrieval fails now (since user is deleted)
    profile_after_delete_res = await client.get("/api/v1/users/me", headers=new_headers)
    assert profile_after_delete_res.status_code == 401


@pytest.mark.asyncio
async def test_role_based_access_control(client):
    """
    Test that users with CUSTOMER role are restricted from admin-only endpoints
    and ADMIN users can successfully access them.
    """
    # Register Admin
    admin_reg = {
        "email": "admin_api@shopsphere.ai",
        "password": "adminSecretPassword123",
        "full_name": "API Admin",
        "role": "ADMIN"
    }
    admin_reg_res = await client.post("/api/v1/auth/register", json=admin_reg)
    assert admin_reg_res.status_code == 201
    
    # Register Customer
    customer_reg = {
        "email": "cust_api_rbac@shopsphere.ai",
        "password": "customerSecretPassword123",
        "full_name": "API Customer RBAC",
        "role": "CUSTOMER"
    }
    cust_reg_res = await client.post("/api/v1/auth/register", json=customer_reg)
    assert cust_reg_res.status_code == 201
    
    # Login Admin
    admin_login_res = await client.post("/api/v1/auth/login", json={
        "email": "admin_api@shopsphere.ai",
        "password": "adminSecretPassword123"
    })
    admin_token = admin_login_res.json()["access_token"]
    
    # Login Customer
    customer_login_res = await client.post("/api/v1/auth/login", json={
        "email": "cust_api_rbac@shopsphere.ai",
        "password": "customerSecretPassword123"
    })
    customer_token = customer_login_res.json()["access_token"]
    
    # 1. Customer attempts to list all users -> Expected: Forbidden (403)
    cust_list_res = await client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert cust_list_res.status_code == 403
    assert cust_list_res.json()["detail"] == "Access denied. Insufficient permissions."
    
    # 2. Admin attempts to list all users -> Expected: Success (200)
    admin_list_res = await client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_list_res.status_code == 200
    users_list = admin_list_res.json()
    assert len(users_list) >= 2  # Admin + Customer
    
    emails = [u["email"] for u in users_list]
    assert "admin_api@shopsphere.ai" in emails
    assert "cust_api_rbac@shopsphere.ai" in emails
