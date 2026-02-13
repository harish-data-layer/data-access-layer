# 🏭 TranAI DAL - Production SAP Integration

This is the **Enterprise Production Version** of the TranAI Data Access Layer.

Unlike the synthetic demo, this version is engineered for real-world SAP integration, security, and scale.

## 🚀 Key Features

### 1. Real SAP Connectivity 🔌
- **OData Connector**: Robust HTTP client for S/4HANA & Gateway services.
- **RFC Connector**: Native BAPI execution for transactional integrity.
- **Resilience**: Built-in retries, timeouts, and circuit breakers.

### 2. Event-Driven Architecture ⚡
- **Kafka Producer**: Publishes change events (`sap.vendor.change`, `sap.order.created`).
- **Compression**: GZIP compression for high-throughput streams.
- **Async Processing**: Decoupled ingestion from API response.

### 3. Enterprise Security 🛡️
- **Secrets Management**: Credentials loaded from environment (Vault-ready).
- **Rate Limiting**: API DDoS protection enabled.
- **Audit Logging**: JSON structured logs for ELK stack integration.

### 4. Production Stack 🏗️
- **PostgreSQL + pgvector**: scalable curated layer with AI search.
- **Redis Cluster**: High-performance caching.
- **Prometheus**: Real-time metrics scraping.

---

## 🛠️ Setup Instructions

### 1. Configuration
Configure your SAP credentials in `.env`:
```bash
SAP_ODATA_URL="https://sap-prod.company.com/..."
SAP_ODATA_USER="SERVICE_ACCOUNT"
SAP_ODATA_PASSWORD="SECURE_PASSWORD"
```

### 2. Start Infrastructure
Deploy the production containers (Postgres, Redis, Kafka, Prometheus):
```bash
docker-compose up -d
```

### 3. Start Application
Launch the high-performance API server:
```bash
npm run dev
```

### 4. Access Dashboard
Open your browser to the production monitoring dashboard:
- **URL**: http://localhost:3001
- **Metrics**: http://localhost:3001/metrics
- **Health**: http://localhost:3001/health

---

## 📊 Monitoring Integration

The system exposes Prometheus metrics at `/metrics`.
Default dashboard available at http://localhost:9091 (user: admin).

## 🧪 Testing Integration

Trigger a manual sync of Vendor Master Data:
```bash
curl -X POST http://localhost:3001/api/v1/sync/vendors
```

## 📜 License
Enterprise License - Copyright 2026 TranAI
