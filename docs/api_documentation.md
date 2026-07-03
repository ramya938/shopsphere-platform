# ShopSphere AI: REST API Documentation

All API traffic to ShopSphere AI is routed through the **API Gateway** on `http://localhost:8000`. The gateway performs rate limiting, caching, and JWT verification.

---

## 🛡️ Authentication & User Service

### 1. Register User
Creates a new customer profile.
* **Method & Route**: `POST /api/v1/auth/register`
* **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Jane Doe",
  "role": "CUSTOMER"
}
```
* **Response (201 Created)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "role": "CUSTOMER",
  "created_at": "2026-06-28T12:00:00Z"
}
```

### 2. User Login
Authenticate credentials to receive access and refresh tokens.
* **Method & Route**: `POST /api/v1/auth/login`
* **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```
* **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### 3. Rotate Tokens
Rotate expired access tokens using a valid refresh token.
* **Method & Route**: `POST /api/v1/auth/refresh`
* **Request Body**:
```json
{
  "refresh_token": "eyJhbGciOi..."
}
```
* **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### 4. Get Current User Profile
Requires a valid bearer token header: `Authorization: Bearer <access_token>`
* **Method & Route**: `GET /api/v1/users/me`
* **Response (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "role": "CUSTOMER",
  "created_at": "2026-06-28T12:00:00Z"
}
```

---

## 📦 Product Service

### 1. List Products
Retrieve catalog products. This endpoint is cached in Redis for 60 seconds.
* **Method & Route**: `GET /api/v1/products`
* **Query Parameters**:
  - `skip` (optional, default: `0`)
  - `limit` (optional, default: `100`)
  - `search` (optional, search filter)
  - `category_id` (optional, UUID category filter)
* **Response (200 OK)**:
```json
[
  {
    "id": "e30e8400-e29b-41d4-a716-446655440111",
    "name": "Wireless Headphones",
    "description": "Premium active noise-cancelling headphones",
    "price": 199.99,
    "inventory_quantity": 42,
    "category_id": "a10e8400-e29b-41d4-a716-446655440222",
    "status": "ACTIVE",
    "created_at": "2026-06-28T12:00:00Z"
  }
]
```

### 2. Create Product (ADMIN only)
Requires admin role access token.
* **Method & Route**: `POST /api/v1/products`
* **Request Body**:
```json
{
  "name": "Mechanical Keyboard",
  "description": "RGB backlighting mechanical keyboard",
  "price": 129.99,
  "inventory_quantity": 15,
  "category_id": "a10e8400-e29b-41d4-a716-446655440222",
  "status": "ACTIVE"
}
```
* **Response (201 Created)**:
```json
{
  "id": "f80e8400-e29b-41d4-a716-446655440333",
  "name": "Mechanical Keyboard",
  "description": "RGB backlighting mechanical keyboard",
  "price": 129.99,
  "inventory_quantity": 15,
  "category_id": "a10e8400-e29b-41d4-a716-446655440222",
  "status": "ACTIVE",
  "created_at": "2026-06-28T12:00:00Z"
}
```

---

## 🛒 Order Service

### 1. Get Shopping Cart
Fetches current user's active shopping cart.
* **Method & Route**: `GET /api/v1/cart`
* **Response (200 OK)**:
```json
{
  "id": "c10e8400-e29b-41d4-a716-446655440444",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-06-28T12:00:00Z",
  "updated_at": "2026-06-28T12:00:00Z",
  "items": [
    {
      "id": "b10e8400-e29b-41d4-a716-446655440555",
      "cart_id": "c10e8400-e29b-41d4-a716-446655440444",
      "product_id": "e30e8400-e29b-41d4-a716-446655440111",
      "quantity": 2,
      "created_at": "2026-06-28T12:00:00Z",
      "updated_at": "2026-06-28T12:00:00Z"
    }
  ]
}
```

### 2. Add Item to Cart
Adds or increments a product quantity inside the active cart.
* **Method & Route**: `POST /api/v1/cart/items`
* **Request Body**:
```json
{
  "product_id": "e30e8400-e29b-41d4-a716-446655440111",
  "quantity": 1
}
```
* **Response (200 OK)**:
*(Returns updated CartResponse object)*

### 3. Checkout Cart
Transition current user's cart items into a formal order. Reserves stock in the Product Service and empties the cart.
* **Method & Route**: `POST /api/v1/orders/checkout`
* **Request Body**:
```json
{
  "shipping_address": "123 Main St, Springfield, IL 62701"
}
```
* **Response (201 Created)**:
```json
{
  "id": "d10e8400-e29b-41d4-a716-446655440666",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_price": 399.98,
  "status": "CREATED",
  "shipping_address": "123 Main St, Springfield, IL 62701",
  "created_at": "2026-06-28T12:00:00Z",
  "items": [
    {
      "id": "e10e8400-e29b-41d4-a716-446655440777",
      "order_id": "d10e8400-e29b-41d4-a716-446655440666",
      "product_id": "e30e8400-e29b-41d4-a716-446655440111",
      "quantity": 2,
      "price": 199.99
    }
  ]
}
```

### 4. Transition Order Status (ADMIN / Customer cancellation)
Transition status of an order (e.g. to mock payment success, process shipment, or cancel).
* **Method & Route**: `PATCH /api/v1/orders/{order_id}/status`
* **Request Body**:
```json
{
  "status": "PAID"
}
```
* **Response (200 OK)**:
*(Returns updated OrderResponse containing new status)*
