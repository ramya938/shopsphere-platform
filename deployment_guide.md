# ShopSphere AI: Production Deployment & Hardening Guide

This document details operational parameters, security hardening configurations, performance optimization tweaks, and telemetry instructions for deploying the **ShopSphere AI** microservice suite in production.

---

## 🏗️ Production Infrastructure Topology

In production, client browsers communicate directly with a public-facing load balancer or reverse proxy (e.g. AWS ALB, Cloudflare, or bare Nginx) which terminates SSL/TLS. This load balancer forwards clean HTTP/HTTPS traffic to the **API Gateway** on port `8000`. 

All core microservices reside inside a private virtual network (such as an AWS VPC or a Docker overlay network) and are not exposed directly to the internet.

---

## 🛡️ Production Hardening Protocols

### 1. Security Configurations
- **Environment Separation**: Ensure the environment variable `ENVIRONMENT` is set to `production` across all service containers. This disables debug logs and prevents FastAPI from exposing auto-generated `/docs` Swagger UIs to unauthenticated public traffic.
- **CORS Policies**: In production, the API Gateway's CORS settings should restrict origins to the specific domain serving the React client. Avoid setting `allow_origins=["*"]`.
- **Database Credentials**: Never commit raw postgres or redis passwords to the repository. Inject database credentials at runtime using secret managers (such as HashiCorp Vault, AWS Secrets Manager, or GitHub Actions Secrets) loaded into container environment variables.
- **JWT Key Rotation**: The `JWT_SECRET_KEY` should be a cryptographically secure 256-bit string generated using `openssl rand -hex 32`. Do not share this key outside the gateway, user, and order services.

### 2. Performance Tuning
- **API Gateway Asynchrony**: The Gateway uses `httpx.AsyncClient` for async reverse proxying. Set `limits=httpx.Limits(max_connections=500, max_keepalive_connections=100)` to optimize connection reuse under high traffic loads.
- **Uvicorn Concurrency**: In Docker containers, FastAPI applications should run via Uvicorn with multiple worker processes. A general rule of thumb for workers is:
  ```
  workers = (2 * CPU_cores) + 1
  ```
  Example startup command in production Dockerfiles:
  ```bash
  CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--no-access-log"]
  ```
- **Database Connection Pool Optimization**: Configure SQLAlchemy connection pooling in child services using:
  - `pool_size=20` (max open persistent connections per worker)
  - `max_overflow=10` (extra temporary connections under burst loads)
  - `pool_recycle=1800` (recycle connections every 30 mins to prevent stale links)
- **Nginx Gzip Compression**: The frontend Nginx container configures gzip compression to minimize JS/CSS bundle payloads delivered to browsers.

---

## 📈 Monitoring & Telemetry Runbooks

### 1. Observability Health Checks
The Gateway exposes a concurrent health-check endpoint:
```http
GET http://localhost:8000/health
```
A monitoring agent (such as Route53, Kubernetes Liveness Probes, or Datadog) should query this endpoint every 10 seconds. Any response with status `degraded` (503 Service Unavailable) should trigger automated container recycling or page engineers.

### 2. Distributed Tracing (`request_id` Propagation)
Every incoming request to the API Gateway is stamped with a unique correlation ID (`X-Request-ID`). This ID is propagated:
- In response headers back to the user interface for client-side logging.
- In downstream headers to child microservices (`user-service`, `product-service`, `order-service`).
- In event headers pushed to Apache Kafka topics during checkout flows.

Ensure all logs output in structured JSON format so that ingestion engines (ELK stack, Splunk, or Grafana Loki) can index `request_id` variables to correlate and trace individual client actions across multiple microservice containers.

---

## 🛠️ Operations Playbooks

### 1. Database Backup & Restores
To execute a hot backup of the postgres schemas inside active containers:
```bash
docker exec -t shopsphere-user-db pg_dumpall -c -U postgres > user_db_backup.sql
```

### 2. Kafka Event Broker Recovers
If Kafka brokers encounter disk space issues or lose synchronization:
1. Verify partition consumer offsets using:
   ```bash
   docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:29092 --describe --group order-group
   ```
2. In case of offset lag, trigger a partition reset:
   ```bash
   docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:29092 --group order-group --reset-offsets --to-earliest --execute --topic order-events
   ```
