# ShopSphere AI - User Microservice

Welcome to the foundation of **ShopSphere AI**, an enterprise-grade Event-Driven Microservices E-Commerce platform. 

This repository contains the **User Service**, designed and built to Netflix-grade standards using **Clean Architecture**, **SOLID principles**, **Repository Pattern**, and asynchronous database access.

---

## Architecture Overview

The User Service is structured according to **Clean Architecture** principles. Dependencies flow inward:

```
                  ┌──────────────────────────────────────────────┐
                  │              Presentation (API)              │
                  │   FastAPI Routers, Exception Handlers, Deps  │
                  └──────────────┬───────────────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────────┐
                  │             Application (Services)           │
                  │      UserService, Pydantic validation        │
                  └──────────────┬───────────────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────────┐
                  │            Domain (Entities/Core)            │
                  │   SQLAlchemy Models, Repository Interfaces   │
                  └──────────────────────────────────────────────┘
                                 ▲
                                 │
                  ┌──────────────┴───────────────────────────────┐
                  │                Infrastructure                │
                  │  DB (AsyncSession), concrete repos, security  │
                  └──────────────────────────────────────────────┘
```

1. **Domain Layer**: Holds pure business entities (`User`, `RefreshToken`) and repository interfaces. Free of external framework dependencies (FastAPI, specific DB connection drivers).
2. **Application Layer**: Directs the business use cases. Orchestrates the repositories and outputs data transfer objects (schemas).
3. **Infrastructure Layer**: Concrete implementation details, containing Async SQLAlchemy database connections, security utilities (Bcrypt, JWT creation), configurations, and logging definitions.
4. **Presentation Layer**: The entry gate for web requests. Leverages FastAPI routers, dependency injection providers (for services/repositories), middleware (request logging, correlation IDs), and exceptions mapping.

---

## Technology Stack

- **Python 3.12** for core backend execution.
- **FastAPI** for asynchronous, high-performance, self-documenting REST APIs.
- **SQLAlchemy 2.0 (Async)** with `asyncpg` for PostgreSQL connection pooling and queries.
- **Alembic** for managing database schema migrations asynchronously.
- **Pydantic v2** for input validation, data parsing, and JSON serialization.
- **JWT (JSON Web Tokens)** for secure, stateless user authorization and token rotation.
- **Passlib & Bcrypt** for secure password hashing.
- **Loguru** for structured JSON/development logging.
- **Docker & Docker Compose** for local deployment and configuration isolation.
- **Pytest & Pytest-Asyncio** for async unit and integration testing.

---

## Directory Structure

```
shopsphere-user-service/
├── .env                  # Environment configurations (local overrides)
├── .env.example          # Template for environment settings
├── .gitignore            # Git exclusion rules
├── Dockerfile            # Multi-stage optimized Docker setup
├── docker-compose.yml    # Development environment compose (app + DB)
├── requirements.txt      # Project library dependencies
├── alembic.ini           # Database migration configuration
├── README.md             # This documentation
├── src/                  # Main source code
│   ├── main.py           # FastAPI application entry point & middlewares
│   ├── config.py         # Config models (Pydantic Settings v2)
│   ├── core/             # Cross-cutting concerns
│   │   ├── exceptions.py # Domain & application custom exceptions
│   │   ├── logging.py    # Loguru logging setup
│   │   └── security.py   # JWT & Hashing security operations
│   ├── domain/           # Core business entities & interfaces
│   │   ├── models.py     # SQLAlchemy ORM models
│   │   └── repository_interfaces.py # Abstract repository interfaces
│   ├── infrastructure/   # Database operations and concrete implementations
│   │   ├── database.py   # Async DB engine & session configuration
│   │   └── repositories/ # Concrete database repositories
│   │       ├── base.py   # Repository base holding AsyncSession
│   │       └── user_repository.py # SQLAlchemy implementations
│   ├── services/         # Application workflow orchestration
│   │   └── user_service.py # UserService containing main domain rules
│   ├── api/              # Presentation layer (HTTP endpoint adapters)
│   │   ├── deps.py       # Dependency injections (Auth, DB, Repos)
│   │   ├── schemas/      # Input/Output Pydantic v2 schemas
│   │   └── v1/           # API endpoints (Auth, Users)
│   └── alembic/          # Database migrations folder
│       ├── env.py        # Async migration runner
│       └── script.py.mako # Migration script template
└── tests/                # Automated testing suite
    ├── conftest.py       # Test configuration and SQLite fixtures
    ├── unit/             # Repository & Service unit tests
    └── integration/      # FastAPI endpoint integration tests
```

---

## Setup & Running Guide

### Prerequisites
- Python 3.12 installed locally, or Docker and Docker Compose installed.

### Option 1: Running with Docker Compose (Recommended)
This runs both the User Service and PostgreSQL database instantly inside network-isolated containers.

1. Build and run the services:
   ```bash
   docker-compose up -d --build
   ```
2. Verify that the server is active:
   ```bash
   curl http://localhost:8000/health
   ```
   Output:
   ```json
   {"status":"healthy","service":"ShopSphere User Service"}
   ```

### Option 2: Running Locally (Development Mode)
1. **Initialize virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variable file**:
   Copy `.env.example` to `.env` and adjust the variables. For local DB access, ensure Postgres is running locally and set `POSTGRES_HOST=localhost`.
4. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```
5. **Start server**:
   ```bash
   uvicorn src.main:app --reload
   ```
   The interactive Swagger API documentation will be available at `http://localhost:8000/docs`.

---

## Database Migrations (Alembic)

Alembic migrations are configured to run asynchronously.

- **Create a new migration script** (Autogenerated based on code changes in models):
  ```bash
  alembic revision --autogenerate -m "describe changes here"
  ```
- **Apply migrations to database**:
  ```bash
  alembic upgrade head
  ```
- **Rollback last migration**:
  ```bash
  alembic downgrade -1
  ```

---

## Running the Test Suite

Tests use `pytest` and `pytest-asyncio` with a transactional, in-memory **SQLite database (`sqlite+aiosqlite`)**. This ensures tests execute in milliseconds without requiring an active PostgreSQL instance, keeping the local workflow completely clean.

Run all tests:
```bash
pytest
```

---

## API Documentation Reference

The microservice implements the following core endpoints:

### Authentication Router (`/api/v1/auth`)
- `POST /register`: Register a new customer. Supports role selection (e.g. `ADMIN`, `CUSTOMER`).
- `POST /login`: Authenticate email and password. Returns JWT Access and Refresh tokens.
- `POST /refresh`: Revokes current refresh token and issues a new access token and rotated refresh token (prevents replay attacks).

### User Management Router (`/api/v1/users`)
- `GET /me`: Returns profile details of the authenticated user.
- `PUT /me`: Modify fields (`email`, `full_name`, `password`) of the active user.
- `DELETE /me`: Deletes the authenticated user account and revokes active tokens.
- `GET /`: Lists all registered users. **Restricted to Admin role only (RBAC)**.
