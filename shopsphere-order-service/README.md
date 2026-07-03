# ShopSphere AI Order Service

The **Order Service** manages shopping carts, checkout operations, direct order placement, and order lifecycle states. It is built using Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, and Loguru.

It communicates asynchronously and statelessly with the other microservices in the **ShopSphere AI** platform.

---

## Architecture & Clean Design

The service implements **Clean Architecture** principles:
- **Domain Layer (`src/domain`)**: Core business objects (`Cart`, `CartItem`, `Order`, `OrderItem`, and `OrderStatus` enum) and repository interfaces. Framework-independent.
- **Application Layer (`src/services`)**: Business logic orchestrators (`CartService`, `OrderService`). Handles transactions, stock validation, inventory updates, and compensating restocks.
- **Infrastructure Layer (`src/infrastructure`)**: Database configuration, concrete repository implementations (async SQLAlchemy), and the HTTP client (`ProductClient`) for calling the Product Service.
- **Presentation Layer (`src/api`)**: FastAPI route declarations, request validation schemas (Pydantic), and global exception mapping handlers.

---

## Database Schema (PostgreSQL)

### 1. Carts (`carts`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` (PK) | Unique cart ID. |
| `user_id` | `UUID` (Unique, Index) | Cart owner's user ID. |
| `created_at` | `DateTime` | Cart creation date. |
| `updated_at` | `DateTime` | Last item modification date. |

### 2. Cart Items (`cart_items`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` (PK) | Cart line item ID. |
| `cart_id` | `UUID` (FK) | Reference to `carts.id` (cascade delete). |
| `product_id` | `UUID` (Index) | Selected product ID. |
| `quantity` | `Integer` | Number of items selected (must be > 0). |
| `created_at` | `DateTime` | Item added timestamp. |
| `updated_at` | `DateTime` | Last quantity modification timestamp. |

### 3. Orders (`orders`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` (PK) | Unique order ID. |
| `user_id` | `UUID` (Index) | Customer who placed the order. |
| `total_price` | `Numeric(10, 2)` | Total price of the checkout. |
| `status` | `Enum/String` | `CREATED`, `PAID`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`. |
| `shipping_address` | `Text` | Shipping destination address. |
| `created_at` | `DateTime` | Order placement timestamp. |
| `updated_at` | `DateTime` | Last status modification timestamp. |

### 4. Order Items (`order_items`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` (PK) | Order line item ID. |
| `order_id` | `UUID` (FK) | Reference to `orders.id` (cascade delete). |
| `product_id` | `UUID` (Index) | Product purchased. |
| `quantity` | `Integer` | Quantity purchased. |
| `price_at_purchase` | `Numeric(10, 2)` | Price of the product locked at checkout. |

---

## Status Transitions & Compensating Transactions

The service validates order state machine transitions:
- `CREATED` -> `PAID`, `CANCELLED`
- `PAID` -> `PROCESSING`, `CANCELLED`
- `PROCESSING` -> `SHIPPED`, `CANCELLED`
- `SHIPPED` -> `DELIVERED`

### Compensating Transactions
- **Checkout Failures**: During order placement, if inventory deduction succeeds but saving the order to the database fails, a compensating **RESTOCK** call is sent to release reserved inventory.
- **Cancellations**: When an order transitions to `CANCELLED` (by the customer or an admin), the service calls `POST /api/v1/products/{id}/restock` on the Product Service to add stock levels back.

---

## REST API Endpoints

### Shopping Cart (`/api/v1/cart`)
- `GET /`: Retrieve the caller's active shopping cart and items.
- `POST /items`: Add a product to the cart (checks stock first).
- `PUT /items/{product_id}`: Update the quantity of an item in the cart.
- `DELETE /items/{product_id}`: Remove an item from the cart.

### Orders (`/api/v1/orders`)
- `POST /checkout`: Place an order using active cart items and clear the cart.
- `POST /`: Directly place an order for a list of items.
- `GET /me`: Get caller's order history.
- `GET /{order_id}`: Get detailed view of an order (owner or ADMIN).
- `GET /`: List all orders placed in the system (ADMIN only).
- `PATCH /{order_id}/status`: Transition an order status (customers can only cancel `CREATED`/`PAID` orders; admins can change to any valid state).

---

## Local Setup & Testing

### Prerequisite Environment Variables (`.env`)
```ini
ENVIRONMENT=development
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=shopsphere_orders
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/shopsphere_orders
PRODUCT_SERVICE_URL=http://localhost:8001
JWT_SECRET_KEY=e83a0adbc87612f0e0c034a706b85bfa17c7689d023bfe4c4246830501867e91
ALGORITHM=HS256
LOG_LEVEL=INFO
```

### Run Tests
Tests are executed on an async in-memory SQLite database:
```bash
venv\Scripts\python -m pytest
```
