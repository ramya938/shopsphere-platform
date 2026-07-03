# ShopSphere AI: System Architecture Diagram

This document contains a visual representation of the **ShopSphere AI** platform. It highlights client interactions, gateway proxy routing, state caching, database boundaries, and asynchronous event streams via Apache Kafka.

---

## 🏗️ Architecture Diagram (Mermaid)

```mermaid
graph TD
    Client["React SPA Client<br>(Vite/TS/Tailwind)<br>Port 3000"] -->|HTTP / HTTPS| Gateway["API Gateway<br>(FastAPI Proxy)<br>Port 8000"]

    subgraph Security & Speed Ingress
        Gateway -->|Cache Check / Rate Limits| Redis[("Redis Caching Store<br>(Cache & Rate Limiting)<br>Port 6379")]
    end

    subgraph Microservices Core
        Gateway -->|Route /api/v1/auth<br>Route /api/v1/users| UserService["User Service<br>(FastAPI / Auth Provider)<br>Port 8010"]
        Gateway -->|Route /api/v1/products<br>Route /api/v1/categories| ProductService["Product Service<br>(FastAPI / Catalog)<br>Port 8011"]
        Gateway -->|Route /api/v1/cart<br>Route /api/v1/orders| OrderService["Order Service<br>(FastAPI / Transactions)<br>Port 8012"]
    end

    subgraph Databases Layer
        UserService -->|Read/Write Profile| UserDB[("PostgreSQL DB<br>shopsphere_users")]
        ProductService -->|Read/Write Catalog| ProductDB[("PostgreSQL DB<br>shopsphere_products")]
        OrderService -->|Read/Write Orders| OrderDB[("PostgreSQL DB<br>shopsphere_orders")]
        PaymentService -->|Read/Write Logs| PaymentDB[("PostgreSQL DB<br>shopsphere_payments")]
    end

    subgraph Async Message Broker
        Kafka[("Apache Kafka<br>(Event Streaming Broker)<br>Port 29092")]
    end

    %% Event Driven Messaging Flows
    OrderService -->|Publish: OrderCreated / OrderCancelled| Kafka
    Kafka -->|Subscribe: OrderCreated| PaymentService["Payment Service<br>(FastAPI / Payments)<br>Port 8013"]
    
    PaymentService -->|Publish: PaymentCompleted / PaymentFailed| Kafka
    Kafka -->|Subscribe: PaymentCompleted / PaymentFailed| OrderService

    Kafka -->|Subscribe: All Transaction Events| NotificationService["Notification Service<br>(FastAPI / Alerts)<br>Port 8014"]
    NotificationService -->|Publish: NotificationSent| Kafka
```

---

## 🔍 Architecture Description

1. **Client Layer**: The client React SPA interacts solely with the API Gateway on port `8000`, securing internal services within the private Docker network.
2. **API Gateway Layer**:
   - **Rate Limiting**: Sliding-window limiter checks Redis on every incoming request, blocking abusers with a `429 Too Many Requests` code.
   - **Response Caching**: Read-only routes (`/api/v1/products` and `/api/v1/categories`) are intercepted, fetching directly from Redis to reduce Postgres load.
   - **JWT Validation**: Authenticates access tokens, injecting standard downstream identity headers (`X-User-Id`, `X-User-Role`).
3. **Core Microservices**: Stateless FastAPI apps running business domains independently with private database storage, satisfying database-per-service isolation principles.
4. **Event-Driven Broker (Kafka)**: Inter-service communication uses asynchronous pub/sub messaging. For instance, checkouts trigger an `OrderCreated` event which the `Payment Service` processes, and payment status updates are sent back to the `Order Service` to advance order states without synchronous blocking calls.
