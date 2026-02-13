# 🚀 TranAI DAL - Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- ✅ **Node.js 18+** installed (`node --version`)
- ✅ **Docker & Docker Compose** installed (`docker --version`)
- ✅ **Git** installed (`git --version`)

---

## Step-by-Step Setup (15 minutes)

### Step 1: Environment Configuration (2 minutes)

```bash
# Copy environment template
cp .env.example .env

# The default values will work for local development
# No need to edit unless you want custom configurations
```

**Key Environment Variables** (already set in .env.example):
- `DATABASE_URL`: PostgreSQL connection string
- `KAFKA_BROKERS`: Kafka broker addresses
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Change this in production!

---

### Step 2: Start Infrastructure (5 minutes)

```bash
# Start all services (PostgreSQL, Kafka, Redis, Prometheus, Grafana, etc.)
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps

# You should see all services as "healthy" or "running"
```

**Services Started**:
- PostgreSQL (port 5432) - Database with pgvector
- Kafka (port 9092) - Event streaming
- Redis (port 6379) - Caching
- Vault (port 8200) - Secrets management
- Prometheus (port 9090) - Metrics
- Grafana (port 3001) - Dashboards
- Elasticsearch (port 9200) - Logging
- Kibana (port 5601) - Log visualization
- Jaeger (port 16686) - Distributed tracing

---

### Step 3: Install Dependencies (3 minutes)

```bash
# Install Node.js dependencies
npm install

# This will install:
# - Prisma (database ORM)
# - Fastify (API framework)
# - Kafka, Redis clients
# - Winston (logging)
# - Prometheus client
# - And 30+ other enterprise packages
```

---

### Step 4: Initialize Database (3 minutes)

```bash
# Generate Prisma client
npm run prisma:generate

# Run database migrations (creates all 8 schemas and 30+ tables)
npm run prisma:migrate dev --name init

# This creates:
# - semantic_layer (entities, attributes, rules, lineage)
# - curated_layer (vendors, invoices, purchase orders)
# - integration_layer (staging, extraction metadata)
# - dq_layer (quality scores, violations)
# - vector_layer (embeddings)
# - event_store (events, snapshots)
# - audit_layer (access logs, AI actions)
# - push_layer (SAP push queue)
```

---

### Step 5: Start the API Server (2 minutes)

```bash
# Development mode (with hot reload)
npm run dev

# You should see:
# ✅ Prisma client initialized
# ✅ Redis client connected
# ✅ Event publisher initialized
# ✅ Server listening on 0.0.0.0:3000
```

---

## ✅ Verify Installation

### 1. Health Check
```bash
curl http://localhost:3000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-13T10:47:00.000Z",
  "uptime": 5.123,
  "environment": "development"
}
```

### 2. API Endpoints
```bash
curl http://localhost:3000/api/v1
```

**Expected Response**:
```json
{
  "name": "TranAI Data Access Layer",
  "version": "1.0.0",
  "description": "Enterprise Three-Layer Data Architecture",
  "endpoints": {
    "semantic": "/api/v1/semantic",
    "curated": "/api/v1/curated",
    "integration": "/api/v1/integration",
    "ai": "/api/v1/ai",
    "lineage": "/api/v1/lineage"
  }
}
```

### 3. Database Check
```bash
# Open Prisma Studio (database GUI)
npm run prisma:studio

# Opens at: http://localhost:5555
# You should see all 8 schemas and tables
```

### 4. Monitoring Dashboards

**Grafana** (Metrics Visualization):
- URL: http://localhost:3001
- Username: `admin`
- Password: `admin`

**Prometheus** (Metrics):
- URL: http://localhost:9090
- Query: `http_requests_total`

**Kibana** (Logs):
- URL: http://localhost:5601

**Jaeger** (Tracing):
- URL: http://localhost:16686

---

## 🧪 Test the System

### 1. Create a Semantic Entity

```bash
curl -X POST http://localhost:3000/api/v1/semantic/entities \
  -H "Content-Type: application/json" \
  -d '{
    "entityName": "Vendor",
    "businessDefinition": "Supplier master data",
    "businessOwner": "Procurement Team",
    "dataSteward": "John Doe",
    "sourceSystem": "SAP_ECC",
    "domain": "Procurement",
    "dataClassification": "Internal",
    "complianceTags": ["GDPR"],
    "retentionPolicy": "7 years"
  }'
```

### 2. Query Entities

```bash
curl http://localhost:3000/api/v1/semantic/entities
```

### 3. Query Curated Data

```bash
curl http://localhost:3000/api/v1/curated/vendors
curl http://localhost:3000/api/v1/curated/invoices
```

### 4. Check Data Quality

```bash
curl http://localhost:3000/api/v1/dq/scores/Vendor
```

### 5. View Audit Logs

```bash
curl http://localhost:3000/api/v1/audit/access
curl http://localhost:3000/api/v1/audit/ai-actions
```

---

## 📊 Load Sample Data (Optional)

### Option 1: Use Existing Excel Data

```bash
# Your synthetic SAP data is already in the repo
# File: huge_synthetic_sap_data_v3.xlsx

# Run the import script (we'll create this next)
npm run import
```

### Option 2: Use Prisma Seed

```bash
# Seed database with sample data
npm run prisma:seed
```

---

## 🛠️ Development Workflow

### Running the Server

```bash
# Development (with hot reload)
npm run dev

# Production build
npm run build
npm start
```

### Database Operations

```bash
# Generate Prisma client after schema changes
npm run prisma:generate

# Create a new migration
npm run prisma:migrate dev --name your_migration_name

# View database in GUI
npm run prisma:studio

# Reset database (WARNING: deletes all data)
npm run prisma:migrate reset
```

### dbt Operations

```bash
# Run dbt transformations
npm run dbt:run

# Run dbt tests
npm run dbt:test

# Generate dbt documentation
npm run dbt:docs
```

### Testing

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

### Code Quality

```bash
# Lint code
npm run lint

# Format code
npm run format
```

---

## 🐛 Troubleshooting

### Issue: Docker services not starting

```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs -f

# Restart services
docker-compose down
docker-compose up -d
```

### Issue: Database connection failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Verify DATABASE_URL in .env matches docker-compose.yml
```

### Issue: Port already in use

```bash
# Find process using port 3000
# Windows:
netstat -ano | findstr :3000

# Kill the process or change API_PORT in .env
```

### Issue: Prisma client not generated

```bash
# Regenerate Prisma client
npm run prisma:generate

# If still failing, delete node_modules and reinstall
rm -rf node_modules
npm install
```

---

## 📚 Next Steps

### 1. Explore the Architecture
- Read **ARCHITECTURE.md** for system design
- Read **IMPLEMENTATION_PLAN.md** for development roadmap

### 2. Load Your Data
- Import your SAP data using the import scripts
- Run dbt transformations to populate curated layer

### 3. Configure SAP Integration
- Update SAP credentials in .env
- Test SAP connectivity
- Set up pull/push workflows

### 4. Set Up Monitoring
- Configure Grafana dashboards
- Set up alerts in Prometheus
- Configure log aggregation in Kibana

### 5. Deploy to Production
- Review **DEPLOYMENT.md** (we'll create this)
- Set up Kubernetes cluster
- Configure CI/CD pipeline

---

## 🎯 Key URLs (Bookmark These!)

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:3000 | - |
| **Health Check** | http://localhost:3000/health | - |
| **Metrics** | http://localhost:3000/metrics | - |
| **Prisma Studio** | http://localhost:5555 | - |
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Kibana** | http://localhost:5601 | - |
| **Jaeger** | http://localhost:16686 | - |
| **Vault** | http://localhost:8200 | Token: dev-token |

---

## ✅ Success Checklist

- [ ] All Docker services are running
- [ ] Database migrations completed
- [ ] API server started successfully
- [ ] Health check returns "healthy"
- [ ] Can query `/api/v1` endpoint
- [ ] Prisma Studio shows all schemas
- [ ] Grafana dashboard accessible
- [ ] Prometheus scraping metrics

---

## 🚀 You're Ready!

Your enterprise-grade Data Access Layer is now running!

**What you have**:
- ✅ Three-layer architecture (Semantic, Curated, Integration)
- ✅ Full governance (lineage, RBAC, audit trail)
- ✅ AI-ready data (embeddings, semantic search)
- ✅ Event sourcing (complete audit trail)
- ✅ Data quality framework
- ✅ Production monitoring (Prometheus, Grafana, ELK, Jaeger)
- ✅ Enterprise security (encryption, Vault)

**Next**: Start building your AI agents on top of this solid foundation!

---

**Need Help?**
- Check **ARCHITECTURE.md** for system design
- Check **IMPLEMENTATION_PLAN.md** for development guide
- Check **BUILD_PROGRESS.md** for current status
- Check logs in `logs/` directory
