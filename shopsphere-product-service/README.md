# ShopSphere AI - Product Microservice

Welcome to the **Product Catalog & Inventory Service** for **ShopSphere AI**—an independent, enterprise-grade FastAPI microservice designed using **Clean Architecture** and **SOLID principles**.

This service manages the product catalog, classifications (categories), search/filtering, and real-time inventory level deductions.

---

## Architecture Overview

The Product Service is designed around loose coupling and independence:

```
                  ┌──────────────────────────────────────────────┐
                  │              Presentation (API)              │
                  │   FastAPI Routers, Exception Handlers, Deps  │
                  └──────────────┬───────────────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────────┐
                  │             Application (Services)           │
                  │   ProductService, CategoryService, Schemas   │
                  └──────────────┬───────────────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────────┐
                  │            Domain (Entities/Core)            │
                  │  SQLAlchemy Models, Repository Interfaces,   │
                  │            Exceptions & Enums                │
                  └──────────────────────────────────────────────┘
                                 ▲
                                 │
                  ┌──────────────┴───────────────────────────────┐
                  │                Infrastructure                │
                  │ DB (AsyncSession), concrete repos, security  │
                  └──────────────────────────────────────────────┘
```

1. **Domain Layer**: Holds model declarations (`Product`, `Category`, `ProductStatus` enum) and repository interface contracts.
2. **Application Layer**: Contains business service operators orchestrating database interactions, category slugs validations, and stock check-outs.
3. **Infrastructure Layer**: Implementation details, database connection setup (Async SQLAlchemy engine), repositories, and token decryption module (stateless JWT decoding using a shared User Service key).
4. **Presentation Layer**: HTTP entry gates (FastAPI endpoint routes), dependency injectors (DB connections, admin role checkers), logging middleware, and global response validators.

---

## Technology Stack

- **Python 3.12** for core backend execution.
- **FastAPI** for high-performance async APIs with OpenAPI docs.
- **SQLAlchemy 2.0 (Async)** with `asyncpg` for PostgreSQL connection pooling and async queries.
- **Alembic** for managing database migrations.
- **Pydantic v2** for validation schemas.
- **JWT (JSON Web Tokens)** for stateless user authentication and role validation.
- **Loguru** for structured logging with correlation IDs.
- **Docker & Docker Compose** for deployment isolation.
- **Pytest & Pytest-Asyncio** for async testing.

---

## Directory Structure

```
shopsphere-product-service/
├── .env                  # Local environment settings overrides
├── .env.example          # Template for environment settings
├── .gitignore            # Git exclusion rules
├── Dockerfile            # Multi-stage optimized Docker setup
├── docker-compose.yml    # Database + Service compose setup
├── requirements.txt      # Project library dependencies
├── alembic.ini           # Database migration configuration
├── pytest.ini            # Pytest configuration file
├── README.md             # This documentation
├── src/                  # Main source code
│   ├── main.py           # FastAPI application & middlewares
│   ├── config.py         # Config models (Pydantic Settings v2)
│   ├── core/             # Cross-cutting concerns
│   │   ├── exceptions.py # Domain & application custom exceptions
│   │   ├── logging.py    # Loguru logging setup
│   │   └── security.py   # JWT decoding (shared secret token verify)
│   ├── domain/           # Core business entities & interfaces
│   │   ├── models.py     # Category and Product SQLAlchemy models
│   │   └── repository_interfaces.py # Abstract repository interfaces
│   ├── infrastructure/   # Database operations and concrete implementations
│   │   ├── database.py   # Async DB engine & session configuration
│   │   └── repositories/ # Concrete database repositories
│   │       ├── base.py   # Base repository class
│   │       ├── category_repository.py # SQLAlchemy Category repository
│   │       └── product_repository.py  # SQLAlchemy Product repository
│   ├── services/         # Application workflow orchestration
│   │   ├── category_service.py # CategoryService (slug generator, crud)
│   │   └── product_service.py  # ProductService (inventory deduct, search)
│   ├── api/              # Presentation layer (HTTP endpoint adapters)
│   │   ├── deps.py       # Dependency injections (Auth, DB, Repos, RBAC)
│   │   ├── schemas/      # Input/Output Pydantic v2 schemas
│   │   └── v1/           # API endpoints (Categories, Products)
│   └── alembic/          # Database migrations folder
└── tests/                # Automated testing suite
```

---

## Setup & Running Guide

### Option 1: Running with Docker Compose (Recommended)
This runs both the Product database (`shopsphere-product-db` on host port 5433) and the Product Service (on host port 8001) in network-isolated containers.

1. Build and start the containers:
   ```bash
   docker-compose up -d --build
   ```
2. Verify the server is active:
   ```bash
   curl http://localhost:8001/health
   ```
   Output:
   ```json
   {"status":"healthy","service":"ShopSphere Product Service"}
   ```

### Option 2: Running Locally (Development Mode)
1. **Initialize virtual environment**:
   ```bash
   py -3.12 -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment file**:
   Copy `.env.example` to `.env` and adjust database credentials. If running PostgreSQL locally, set `POSTGRES_HOST=localhost`.
4. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```
5. **Start server**:
   ```bash
   uvicorn src.main:app --port 8001 --reload
   ```

---

## Database Migrations (Alembic)

To update database tables:
- **Autogenerate a migration revision**:
  ```bash
  alembic revision --autogenerate -m "describe changes"
  ```
- **Apply migrations**:
  ```bash
  alembic upgrade head
  ```

---

## Running the Test Suite

Tests run on an in-memory async SQLite database (`sqlite+aiosqlite`) to keep test cycles fast and independent of PostgreSQL.

Run tests:
```bash
pytest
```

---

## API Documentation Reference

The service is active on port `8001` and implements the following endpoints:

### Categories Endpoint (`/api/v1/categories`)
- `POST /`: Create Category. **Restricted to Admin**.
- `GET /`: Retrieve all categories. **Public access**.
- `GET /{category_id}`: Retrieve single category. **Public access**.
- `PUT /{category_id}`: Modify category. **Restricted to Admin**.
- `DELETE /{category_id}`: Delete category. **Restricted to Admin**.

### Products Endpoint (`/api/v1/products`)
- `POST /`: Create Product. **Restricted to Admin**.
- `GET /`: Query and search products. Supports filtering by:
  - `search` (text search in name/description)
  - `category_id` (category UUID)
  - `min_price` / `max_price`
  - `status` (`DRAFT`, `ACTIVE`, `OUT_OF_STOCK`)
  - `sort_by` (`price`, `created_at`, `name`) & `sort_order` (`asc`, `desc`)
  - `skip` & `limit` (pagination offsets)
- `GET /{product_id}`: Retrieve product details. **Public access**.
- `PUT /{product_id}`: Modify product details. **Restricted to Admin**.
- `DELETE /{product_id}`: Delete product. **Restricted to Admin**.
- `POST /{product_id}/deduct`: Deduct stock from inventory after order checkouts. **Restricted to Admin**.
- `POST /{product_id}/restock`: Restock quantity levels. **Restricted to Admin**.
