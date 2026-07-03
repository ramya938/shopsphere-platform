# ShopSphere AI: Event-Driven Microservices Platform

ShopSphere AI is a production-grade, event-driven e-commerce platform designed with a decoupled microservice architecture. It combines asynchronous HTTP proxying, high-throughput message streaming, resilient payment fulfillment, and a modern, state-cached user interface.

---

## 🏗️ System Architecture & Layout

The platform consists of seven fully dockerized service containers communicating via synchronous REST APIs and asynchronous pub/sub event streams:

```
shopsphere-platform/
├── docs/                      # Production API & System Diagrams
│   ├── architecture_diagram.md # System flowcharts (Mermaid)
│   ├── er_diagram.md          # Consolidated DB schemas (Mermaid)
│   ├── api_documentation.md   # API route details and payloads
│   └── portfolio_showcase.md  # Interview Q&As & Resume bullet points
├── shopsphere-frontend/       # React + Vite + TypeScript Client (Nginx)
├── shopsphere-gateway/        # Redis-cached secure reverse proxy (FastAPI)
├── shopsphere-user-service/   # Identity and access control provider (Postgres)
├── shopsphere-product-service/# Inventory & category catalog engine (Postgres)
├── shopsphere-order-service/  # Carts & checkouts publisher (Postgres & Kafka)
├── shopsphere-payment-service/# Asynchronous payment processor (Postgres & Kafka)
└── shopsphere-notification-service/# Asynchronous event logger (Kafka)
```

For a visual breakdown of service nodes and network links, review the [docs/architecture_diagram.md](file:///c:/Users/r8765/Desktop/shopsphere-platform/docs/architecture_diagram.md).

---

## ⚡ Core Features

- **Decoupled Event-Driven Flow**: Checkouts publish `OrderCreated` messages to Apache Kafka. The Payment Service processes transactions asynchronously and publishes `PaymentCompleted` or `PaymentFailed` events, resolving state changes without blocking client threads.
- **Resilient Retry & DLQ Policies**: Payment processors implement exponential backoff retry loops. Repeatedly failing transactions are dispatched to a Dead Letter Queue (`payment-dlq`) to maintain data integrity and notify administrators.
- **Rate-Limiting Ingress**: API Gateway uses a Redis sliding window rate-limiter to protect services (100 req/min for authenticated users, 20 req/min for anonymous clients).
- **Fast Catalog Caching**: High-frequency read queries (`/api/v1/products` and `/api/v1/categories`) are cached in Redis (60s TTL), cutting response latency to < 5ms.
- **Stateful JWT Client-Rotation**: React frontend utilizes Axios interceptors to automatically rotate expired access tokens using the refresh token endpoint, ensuring uninterrupted sessions.

---

## 🚀 Quickstart & Docker Orchestration

Ensure you have **Docker** and **Docker Compose V2** installed. To boot the entire 12-container network:

```bash
docker compose up --build -d
```

This will run and link:
- **Zookeeper & Kafka**: For message streaming.
- **Redis**: Caching & rate limiting store.
- **Four PostgreSQL Databases**: Isolated data schemas for user, product, order, and payment services.
- **API Gateway**: Ingress proxy listening on port `8000`.
- **React Frontend**: Served via Nginx on `http://localhost:3000`.

To verify container statuses:
```bash
docker compose ps
```

---

## 🛡️ Documentation Library

For a detailed walkthrough of configurations, database structures, and career assets, reference the files below:
- **REST API Specs**: [docs/api_documentation.md](file:///c:/Users/r8765/Desktop/shopsphere-platform/docs/api_documentation.md)
- **Database ER Diagram**: [docs/er_diagram.md](file:///c:/Users/r8765/Desktop/shopsphere-platform/docs/er_diagram.md)
- **Architecture Flowcharts**: [docs/architecture_diagram.md](file:///c:/Users/r8765/Desktop/shopsphere-platform/docs/architecture_diagram.md)
- **Operations Manual**: [deployment_guide.md](file:///c:/Users/r8765/Desktop/shopsphere-platform/deployment_guide.md)
- **Interview & Career Assets**: [docs/portfolio_showcase.md](file:///c:/Users/r8765/Desktop/shopsphere-platform/docs/portfolio_showcase.md)

---

## 🧪 Service Testing

Every Python backend service contains a database-independent asynchronous unit test suite running on SQLite:

```bash
# Example: Run Gateway test suite
cd shopsphere-gateway
pip install -r requirements.txt
python -m pytest
```

All 6 microservices tests compile and pass inside the automated **GitHub Actions CI** environment (`.github/workflows/ci.yml`).
