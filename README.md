# 🚀 TranAI Data Access Layer (DAL)

## Enterprise Three-Layer Data Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green)](https://nodejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue)](https://www.postgresql.org/)

**Production-grade Data Access Layer** for AI platforms with full governance, lineage, and bidirectional SAP integration.

---

## 📚 Documentation

- **[Architecture Document](./ARCHITECTURE.md)** - Complete system architecture
- **[Implementation Plan](./IMPLEMENTATION_PLAN.md)** - 12-week development roadmap
- **[API Documentation](./docs/API.md)** - REST API reference (auto-generated)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  AI Agents | Analytics | Dashboards             │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ REST APIs
                              │
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: Semantic Layer (Metadata & Business Rules)            │
│  LAYER 2: Curated Layer (AI-Ready, Validated Data)              │
│  LAYER 3: Integration Layer (Pull from SAP, Push to SAP)        │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Kafka Events
                              │
┌─────────────────────────────────────────────────────────────────┐
│              SAP | External Systems | Portals                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🧠 AI-First Design
- **Pre-computed embeddings** for semantic search
- **Vector similarity** search (pgvector)
- **AI action logging** with explainability
- **Confidence scoring** for AI-generated data

### 🔐 Enterprise Governance
- **Field-level lineage** tracking
- **RBAC** with role-based permissions
- **Data classification** (Public, Confidential, PII)
- **Compliance tags** (GDPR, SOX, HIPAA)
- **7+ year audit trail**

### 📊 Data Quality
- **Multi-dimensional DQ scoring** (Completeness, Accuracy, Validity, etc.)
- **Great Expectations** integration
- **dbt tests** for validation
- **Real-time DQ monitoring**

### 🔄 SAP Integration
- **Bidirectional sync** (Pull & Push)
- **OData, BAPI, IDoc** support
- **Event sourcing** for full audit trail
- **Retry with exponential backoff**
- **Manual approval workflow** for critical actions

### 📈 Observability
- **Prometheus** metrics
- **Grafana** dashboards
- **OpenTelemetry** distributed tracing
- **ELK stack** for logging
- **Real-time monitoring**

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Docker** & **Docker Compose** ([Download](https://www.docker.com/))
- **Git** ([Download](https://git-scm.com/))

### 1. Clone Repository

```bash
git clone git@github.com:harish-data-layer/data-access-layer.git
cd data-access-layer
git checkout dal-setup
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# (Database URL, SAP credentials, etc.)
```

### 3. Start Infrastructure

```bash
# Start all services (PostgreSQL, Kafka, Redis, etc.)
docker-compose up -d

# Check service health
docker-compose ps
```

### 4. Install Dependencies

```bash
npm install
```

### 5. Database Setup

```bash
# Generate Prisma client
npm run prisma:generate

# Run migrations
npm run prisma:migrate

# (Optional) Seed with sample data
npm run prisma:seed
```

### 6. Start Development Server

```bash
npm run dev
```

The API will be available at: **http://localhost:3000**

---

## 📡 API Endpoints

### Semantic Layer
```
GET    /api/v1/semantic/entities
GET    /api/v1/semantic/entities/:id
GET    /api/v1/semantic/lineage/:entity/:field
```

### Curated Layer
```
GET    /api/v1/curated/vendors
POST   /api/v1/curated/vendors
GET    /api/v1/curated/invoices
GET    /api/v1/curated/dq/scores/:entity
```

### Integration Layer
```
POST   /api/v1/integration/pull/:source/:entity
GET    /api/v1/integration/extraction/:id
POST   /api/v1/integration/push/:target/:entity
```

**Full API documentation**: http://localhost:3000/docs (Swagger UI)

---

## 🧪 Testing

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

---

## 📊 Monitoring

### Prometheus Metrics
http://localhost:9090

### Grafana Dashboards
http://localhost:3001 (admin/admin)

### Kibana (Logs)
http://localhost:5601

### Jaeger (Tracing)
http://localhost:16686

### Prisma Studio (Database UI)
```bash
npm run prisma:studio
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Runtime** | Node.js 18+ |
| **Language** | TypeScript 5.3 |
| **Database** | PostgreSQL 15 + pgvector |
| **ORM** | Prisma |
| **API Framework** | Fastify |
| **Event Streaming** | Apache Kafka |
| **Caching** | Redis |
| **Secrets** | HashiCorp Vault |
| **Transformations** | dbt |
| **Data Quality** | Great Expectations |
| **Metrics** | Prometheus + Grafana |
| **Logging** | ELK Stack |
| **Tracing** | OpenTelemetry + Jaeger |
| **Containers** | Docker + Kubernetes |

---

## 📂 Project Structure

```
dal-setup/
├── prisma/
│   ├── schema.prisma          # Multi-schema database models
│   └── migrations/            # Database migrations
├── src/
│   ├── services/
│   │   ├── semantic/          # Semantic layer services
│   │   ├── curated/           # Curated layer services
│   │   ├── integration/       # Integration layer services
│   │   └── ai/                # AI-specific services
│   ├── api/
│   │   ├── routes/            # API route handlers
│   │   └── middleware/        # Auth, RBAC, audit
│   ├── utils/                 # Helper functions
│   ├── config/                # Configuration
│   └── types/                 # TypeScript types
├── dbt/
│   ├── models/                # dbt transformation models
│   └── tests/                 # dbt data quality tests
├── python/
│   ├── sap_connectors/        # SAP OData/BAPI clients
│   └── data_quality/          # Great Expectations
├── monitoring/
│   ├── prometheus.yml         # Metrics config
│   └── grafana/               # Dashboards
├── kubernetes/                # K8s manifests
├── scripts/                   # Utility scripts
├── tests/                     # Unit & integration tests
├── docker-compose.yml         # Local development
├── ARCHITECTURE.md            # System architecture
└── IMPLEMENTATION_PLAN.md     # Development roadmap
```

---

## 🔐 Security

### Authentication
- **JWT tokens** with role claims
- **OAuth 2.0** for external integrations
- **mTLS** for SAP connectivity

### Data Protection
- **Field-level encryption** (AES-256)
- **Tokenization** for PII
- **Key management** via HashiCorp Vault
- **TLS 1.3** for data in transit

### Compliance
- **GDPR** right to erasure
- **SOX** financial controls
- **Audit logging** (7+ years)
- **Data classification** enforcement

---

## 🚢 Deployment

### Docker (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Apply manifests
kubectl apply -f kubernetes/

# Check status
kubectl get pods -n tranai-dal
```

### Cloud Deployment
- **AWS**: EKS + RDS + MSK
- **Azure**: AKS + PostgreSQL + Event Hubs
- **GCP**: GKE + Cloud SQL + Pub/Sub

---

## 📈 Performance

| Metric | Target | Actual |
|--------|--------|--------|
| **API Latency (p95)** | < 200ms | TBD |
| **Data Quality Score** | > 95% | TBD |
| **SAP Sync Success** | > 99.5% | TBD |
| **Uptime** | 99.9% | TBD |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **TranAI Team** - Architecture & Development
- **OpenMetadata** - Data catalog
- **dbt Labs** - Transformation framework
- **Great Expectations** - Data quality

---

## 📞 Support

- **Documentation**: [./docs](./docs)
- **Issues**: [GitHub Issues](https://github.com/harish-data-layer/data-access-layer/issues)
- **Email**: support@tranai.com

---

