# ShopSphere AI: Entity-Relationship (ER) Diagram

This document describes the database schemas across the **ShopSphere AI** platform. Because the platform follows the *Database-per-Service* pattern, these tables are distributed across four isolated PostgreSQL databases:
1. `shopsphere_users` (User Service)
2. `shopsphere_products` (Product Service)
3. `shopsphere_orders` (Order Service)
4. `shopsphere_payments` (Payment Service)

---

## 📊 Database Schemas (Mermaid ERD)

```mermaid
erDiagram
    %% USER SERVICE DATABASE
    USERS {
        uuid id PK
        string email UNIQUE
        string hashed_password
        string full_name
        string role "ADMIN | CUSTOMER"
        timestamp created_at
        timestamp updated_at
    }

    %% PRODUCT SERVICE DATABASE
    CATEGORIES {
        uuid id PK
        string name UNIQUE
        string description
        timestamp created_at
        timestamp updated_at
    }
    PRODUCTS {
        uuid id PK
        string name
        string description
        decimal price
        integer inventory_quantity
        uuid category_id FK
        string status "ACTIVE | INACTIVE"
        timestamp created_at
        timestamp updated_at
    }

    CATEGORIES ||--o{ PRODUCTS : "contains"

    %% ORDER SERVICE DATABASE
    CARTS {
        uuid id PK
        uuid user_id UNIQUE
        timestamp created_at
        timestamp updated_at
    }
    CART_ITEMS {
        uuid id PK
        uuid cart_id FK
        uuid product_id
        integer quantity
        timestamp created_at
        timestamp updated_at
    }
    ORDERS {
        uuid id PK
        uuid user_id
        decimal total_price
        string status "CREATED | PAID | PROCESSING | SHIPPED | DELIVERED | CANCELLED"
        string shipping_address
        timestamp created_at
        timestamp updated_at
    }
    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid product_id
        integer quantity
        decimal price
        timestamp created_at
        timestamp updated_at
    }

    CARTS ||--o{ CART_ITEMS : "holds"
    ORDERS ||--o{ ORDER_ITEMS : "holds"

    %% PAYMENT SERVICE DATABASE
    PAYMENTS {
        uuid id PK
        uuid order_id UNIQUE
        decimal amount
        string status "COMPLETED | FAILED | PENDING"
        string transaction_id UNIQUE
        string error_message
        timestamp created_at
        timestamp updated_at
    }
```

---

## 🔑 Key Relationships & Distributed Integrity

- **Database-per-Service Isolation**: References to foreign models outside a service's database boundary are stored as raw UUID values (e.g. `CART_ITEMS.product_id` or `CARTS.user_id`). Integrity is enforced at the application layer through API catalog checks and Kafka event messaging, not database-level foreign key constraints.
- **Order Details**: An `ORDER` contains multiple `ORDER_ITEMS`. During cart checkouts, items are mapped from `CART_ITEMS` into `ORDER_ITEMS` with static prices capturing the price at the time of purchase.
- **Payments**: The `PAYMENTS` table links one-to-one with the `ORDERS` table via `order_id` in a separate schema, allowing auditing and tracking of payment transitions independently.
