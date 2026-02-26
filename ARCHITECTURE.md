# 🏗️ TranAI Data Access Layer - Enterprise Architecture

## 📋 Executive Summary

This document defines the **production-grade, enterprise-level Three-Layer Data Architecture** for the TranAI Data Access Layer (DAL). This architecture supports AI platforms, AI agents, analytics, and bidirectional SAP integration with full governance, lineage, and explainability.

---

## 🎯 Architecture Principles

1. **Separation of Concerns**: Clear boundaries between semantic meaning, data preparation, and system integration
2. **AI-First Design**: Optimized for LLM consumption and AI agent interaction
3. **Full Auditability**: Complete lineage from source → curated → AI action → target system
4. **Real-Time Capability**: Event-driven architecture with streaming support
5. **Enterprise Governance**: RBAC, data classification, compliance, and quality enforcement
6. **Scalability**: Microservices-based, containerized, cloud-native

---

## 🏛️ Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONSUMPTION LAYER                            │
│  AI Agents | Analytics | Dashboards | External Systems          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ REST APIs / GraphQL
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   LAYER 1: SEMANTIC LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Metadata   │  │   Business   │  │  AI Context  │          │
│  │  Repository  │  │    Rules     │  │  & Ontology  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  • Entity definitions  • Validation rules  • LLM hints          │
│  • Data classification • Constraints       • Embeddings         │
│  • Lineage mapping     • SLAs              • Reasoning scope    │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Metadata enrichment
                              │
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 2: AI-READY / CURATED LAYER                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Curated    │  │  Data Quality│  │    Vector    │          │
│  │   Tables     │  │   Scoring    │  │    Store     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  • Clean, validated data  • DQ metrics  • Pre-computed          │
│  • Standardized formats   • Masking     • embeddings            │
│  • SCD Type 2 history     • Encryption  • Semantic search       │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ dbt transformations
                              │
┌─────────────────────────────────────────────────────────────────┐
│            LAYER 3: INTEGRATION LAYER (PULL & PUSH)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Staging     │  │  Event       │  │   Audit      │          │
│  │  Tables      │  │  Store       │  │   Trail      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  • Raw ingestion      • Kafka events   • Full lineage          │
│  • CDC tracking       • Event sourcing • Access logs           │
│  • Push queue         • Replay         • Compliance            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Kafka / Message Queue
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                              │
│     SAP (OData/BAPI/IDoc) | Portals | APIs | Databases         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Layer 1: Semantic Layer (Metadata Fabric)

### Purpose
Define **what the data means** from business and AI perspectives. Acts as the single source of truth for interpretation.

### Components

#### 1.1 Metadata Repository
**Schema**: `semantic_layer`

**Tables**:
- `entities` - Business entity definitions
- `attributes` - Field-level metadata
- `business_rules` - Validation and constraint rules
- `data_classification` - Sensitivity and compliance tags
- `lineage_map` - Source-to-curated mappings
- `ai_context` - LLM interpretation hints
- `entity_versions` - Temporal versioning

**Key Fields**:
```sql
entities:
  - entity_id (PK)
  - entity_name
  - business_definition
  - business_owner
  - data_steward
  - source_system
  - domain (Finance, Procurement, HR)
  - data_classification (Public, Internal, Confidential, PII)
  - compliance_tags (GDPR, SOX, HIPAA)
  - retention_policy
  - version_id
  - effective_from / effective_to
  - ai_reasoning_scope
  - embedding_namespace
```

#### 1.2 Business Rules Engine
**Three-layer rule representation**:
1. **SQL/dbt tests** - Deterministic enforcement
2. **JSON Schema** - Machine validation
3. **Natural Language** - AI interpretation

**Example**:
```json
{
  "rule_id": "VND_001",
  "rule_name": "Vendor GST Validation",
  "sql_expression": "LENGTH(gst) = 15 AND gst ~ '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'",
  "json_schema": { "type": "string", "pattern": "^[0-9]{2}[A-Z]{5}..." },
  "ai_explanation": "GST number must be 15 characters following Indian GST format"
}
```

#### 1.3 Semantic Versioning
- **Version control** for all entity definitions
- **Backward compatibility** via view abstraction
- **Breaking change flags**
- **Temporal validity** (effective_from/to)

### Technology Stack
- **PostgreSQL** (metadata storage)
- **OpenMetadata / DataHub** (catalog UI)
- **dbt** (documentation generation)

---

## 🧠 Layer 2: AI-Ready / Curated Layer

### Purpose
Materialize **clean, validated, AI-optimized data** ready for consumption by AI agents, analytics, and APIs.

### Components

#### 2.1 Curated Data Store
**Schema**: `curated_layer`

**Tables** (transformed from raw):
- `curated_vendors`
- `curated_purchase_orders`
- `curated_invoices`
- `curated_payments`
- `curated_contracts`

**Features**:
- **Standardized formats** (dates, currencies, addresses)
- **Denormalized views** for AI performance
- **SCD Type 2** for historical tracking
- **Computed fields** (aging, risk scores)

#### 2.2 Data Quality Framework
**Schema**: `dq_layer`

**Tables**:
- `dq_scores` - Per-dataset/column/record quality metrics
- `dq_rules` - Quality validation definitions
- `dq_violations` - Failed quality checks

**Dimensions**:
- Completeness
- Accuracy
- Consistency
- Validity
- Timeliness
- Uniqueness

**DQ Score Calculation**:
```python
DQ_Score = (
  0.25 * completeness +
  0.25 * accuracy +
  0.20 * consistency +
  0.15 * validity +
  0.10 * timeliness +
  0.05 * uniqueness
)
```

**Tools**:
- **Great Expectations** (validation)
- **dbt tests** (enforcement)
- **Monte Carlo** (monitoring - optional)

#### 2.3 Sensitive Data Protection
**Strategy**:
| Data Type | Method | Reversible |
|-----------|--------|------------|
| Identifiers (PAN, Aadhaar) | Tokenization | Yes (RBAC) |
| Analytics (aggregates) | Hashing | No |
| Operational (bank accounts) | Encryption (AES-256) | Yes (KMS) |
| AI Training | Anonymization | No |

**Implementation**:
- **AWS KMS / HashiCorp Vault** for key management
- **Attribute-Based Access Control (ABAC)**
- **Field-level encryption** in PostgreSQL

#### 2.4 Vector Store (AI Optimization)
**Schema**: `vector_layer`

**Tables**:
- `vendor_embeddings`
- `invoice_text_embeddings`
- `contract_embeddings`

**Technology**:
- **pgvector** (PostgreSQL extension) - for simplicity
- **Weaviate / Pinecone** (for scale)

**Pre-computed embeddings** for:
- Vendor descriptions
- Invoice line items
- Contract clauses
- Notes and comments

### Technology Stack
- **PostgreSQL** (curated data)
- **dbt** (transformations)
- **Great Expectations** (DQ)
- **pgvector** (embeddings)

---

## 🔄 Layer 3: Integration Layer (Pull & Push)

### Purpose
Manage **bidirectional data flow** between external systems and the DAL with full lineage and audit trail.

### Components

#### 3.1 Staging Layer (Inbound Pull)
**Schema**: `integration_layer`

**Tables**:
- `staging_vendors`
- `staging_purchase_orders`
- `staging_invoices`
- `extraction_metadata` - CDC tracking
- `reconciliation_log` - Data validation

**Extraction Metadata**:
```sql
extraction_metadata:
  - extraction_id (PK)
  - source_system (SAP_ECC, SAP_S4, Portal)
  - entity_name
  - extraction_type (FULL, INCREMENTAL)
  - last_sync_timestamp
  - records_extracted
  - records_loaded
  - status (SUCCESS, FAILED, PARTIAL)
  - error_log
```

**SAP Connectivity**:
| Interface | Use Case |
|-----------|----------|
| **OData** | Modern S/4HANA systems |
| **RFC/BAPI** | Legacy ECC systems |
| **CDC (SLT/Debezium)** | Real-time incremental sync |

**Reliability**:
- Circuit breaker pattern
- Exponential backoff retry
- Idempotent ingestion

#### 3.2 Push Queue (Outbound)
**Schema**: `push_layer`

**Tables**:
- `push_queue` - Pending SAP posts
- `push_staging` - Pre-validation
- `push_approval` - Manual approval workflow
- `push_log` - Execution history

**Push Workflow**:
```
AI Action → Validation → Approval (if critical) → SAP Push → Confirmation
```

**SAP Posting Interfaces**:
| Interface | Use Case |
|-----------|----------|
| **BAPI** | Transactional consistency (invoice posting) |
| **IDoc** | Async messaging (bulk updates) |
| **OData** | Lightweight operations |

**Error Handling**:
- Retry queue with exponential backoff
- Manual correction workflow
- Dead letter queue (DLQ)

#### 3.3 Event Store (Event Sourcing)
**Schema**: `event_store`

**Tables**:
- `events` - Immutable event log
- `event_snapshots` - State reconstruction
- `event_replay_log` - Replay tracking

**Event Structure**:
```json
{
  "event_id": "uuid",
  "event_type": "INVOICE_CREATED",
  "aggregate_id": "INV-12345",
  "timestamp": "2026-02-13T10:35:00Z",
  "actor": "AI_AGENT_VIM",
  "payload": { "full": {...}, "delta": {...} },
  "correlation_id": "trace-xyz",
  "metadata": { "source": "SAP", "lineage": [...] }
}
```

**Retention**:
- Operational: 90 days (hot storage)
- Audit: 7+ years (cold storage)

**Technology**:
- **Apache Kafka** (event streaming)
- **EventStoreDB** (optional dedicated store)

#### 3.4 Audit Trail
**Schema**: `audit_layer`

**Tables**:
- `data_access_log` - Who accessed what, when
- `data_change_log` - All mutations
- `ai_action_log` - AI-generated actions
- `approval_log` - Human approvals

**Retention**: Minimum 7 years (compliance)

### Technology Stack
- **Apache Kafka** (event streaming)
- **Python** (SAP connectors - pyrfc, OData)
- **Node.js** (orchestration)
- **PostgreSQL** (staging, queues, audit)

---

## 🔐 Cross-Layer Governance

### Data Lineage
**Granularity**: Field-level

**Tracking**:
```
SAP.VENDOR.NAME → staging_vendors.name → curated_vendors.vendor_name → AI Agent → SAP.VENDOR.NAME (update)
```

**Technology**:
- **OpenLineage** (standard)
- **Marquez** (lineage UI)
- **dbt** (transformation lineage)

**API**: `/api/lineage/{entity}/{field}`

### Role-Based Access Control (RBAC)

**Roles**:
| Role | Permissions |
|------|-------------|
| **Data Engineer** | Full access to integration & curated layers |
| **Data Steward** | Metadata management, DQ rules |
| **AI Agent** | Read curated, write to push queue (scoped) |
| **Analyst** | Read curated (filtered by classification) |
| **Admin** | Full system access |
| **Auditor** | Read-only audit logs |

**Granularity**:
- Field-level permissions
- Entity-level permissions
- AI agents have scoped, time-limited tokens

**Implementation**:
- **PostgreSQL Row-Level Security (RLS)**
- **JWT tokens** with role claims
- **API Gateway** (rate limiting, auth)

### Data Classification & Compliance

**Classification Levels**:
- **Public**: No restrictions
- **Internal**: Employees only
- **Confidential**: Need-to-know basis
- **Restricted**: Legal/compliance only
- **PII**: GDPR/privacy controls

**Compliance Tags**:
- GDPR (EU data protection)
- SOX (financial controls)
- HIPAA (healthcare - if applicable)

**Enforcement**:
- Automatic masking based on classification
- Audit logging for PII access
- Retention policy automation

---

## 🛠️ Technology Stack Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | PostgreSQL 15+ | Multi-schema data store |
| **ORM** | Prisma | Schema management |
| **Transformations** | dbt | Curated layer modeling |
| **Event Streaming** | Apache Kafka | Real-time integration |
| **Message Queue** | Kafka (primary), RabbitMQ (fallback) | Async processing |
| **Vector DB** | pgvector (simple), Weaviate (scale) | AI embeddings |
| **Data Quality** | Great Expectations | Validation framework |
| **Metadata Catalog** | OpenMetadata / DataHub | Governance UI |
| **Lineage** | OpenLineage + Marquez | Lineage tracking |
| **SAP Connectivity** | Python (pyrfc, OData), Node.js | Bidirectional sync |
| **API Layer** | Node.js (Express/Fastify) | REST APIs |
| **Orchestration** | Airflow / Prefect | Workflow scheduling |
| **Monitoring** | Prometheus + Grafana | Metrics |
| **Logging** | ELK Stack (Elasticsearch, Logstash, Kibana) | Centralized logs |
| **Tracing** | OpenTelemetry | Distributed tracing |
| **Key Management** | HashiCorp Vault / AWS KMS | Encryption keys |
| **Container Orchestration** | Kubernetes | Deployment |
| **IaC** | Terraform | Infrastructure as code |

---

## 🚀 Deployment Architecture

### Microservices Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│              (Rate Limiting, Auth, Routing)                      │
└─────────────────────────────────────────────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Semantic │  │ Curated  │  │Integration│  │  AI      │
    │ Service  │  │ Service  │  │ Service   │  │ Service  │
    └──────────┘  └──────────┘  └──────────┘  └──────────┘
           │              │              │              │
           └──────────────┴──────────────┴──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │  (Multi-schema)  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Kafka Cluster  │
                    └──────────────────┘
```

### Container Strategy
- **Docker** for containerization
- **Kubernetes** for orchestration
- **Helm** for package management

### Environment Strategy
| Environment | Schema Prefix | Purpose |
|-------------|---------------|---------|
| **dev** | `dev_semantic`, `dev_curated`, `dev_integration` | Development |
| **staging** | `stg_semantic`, `stg_curated`, `stg_integration` | Pre-production |
| **prod** | `semantic_layer`, `curated_layer`, `integration_layer` | Production |

### Deployment Strategy
- **Blue-Green Deployments** (zero downtime)
- **Feature Flags** (gradual rollouts)
- **Automated Rollback** (on health check failures)
- **Canary Releases** (10% → 50% → 100%)

---

## 📡 API Architecture

### REST API Structure

**Base URL**: `https://api.tranai.com/dal/v1`

**Endpoints**:

#### Semantic Layer
```
GET    /semantic/entities
GET    /semantic/entities/{entity_id}
GET    /semantic/entities/{entity_id}/attributes
GET    /semantic/entities/{entity_id}/rules
GET    /semantic/lineage/{entity}/{field}
```

#### Curated Layer
```
GET    /curated/vendors
GET    /curated/vendors/{vendor_id}
POST   /curated/vendors (AI-generated)
GET    /curated/invoices
GET    /curated/invoices/{invoice_id}
GET    /curated/dq/scores/{entity}
```

#### Integration Layer
```
POST   /integration/pull/{source}/{entity}
GET    /integration/extraction/status/{extraction_id}
POST   /integration/push/{target}/{entity}
GET    /integration/push/queue
POST   /integration/push/approve/{push_id}
```

#### AI Layer
```
POST   /ai/embeddings/search
GET    /ai/context/{entity}
POST   /ai/action/log
```

### API Features
- **GraphQL-style field selection** (via query params)
- **Bulk operations** (`POST /curated/vendors/bulk`)
- **Async processing** (long-running jobs return job_id)
- **Webhooks** (push notifications on events)
- **Idempotency keys** (prevent duplicate operations)
- **Rate limiting** (per role/tenant)
- **API versioning** (v1, v2)

### Authentication & Authorization
- **JWT tokens** with role claims
- **OAuth 2.0** for external integrations
- **API keys** for service-to-service
- **mTLS** for SAP connectivity

---

## 📊 Monitoring & Observability

### Metrics (Prometheus + Grafana)
- **Pipeline Health**: Success/failure rates, latency
- **Data Quality**: DQ scores over time, violation trends
- **API Performance**: Request rate, latency, error rate
- **SAP Connectivity**: Connection status, sync lag
- **Kafka**: Consumer lag, throughput

### Logging (ELK Stack)
- **Application logs**: Structured JSON logs
- **Audit logs**: Compliance-ready format
- **Error logs**: Stack traces, context

### Tracing (OpenTelemetry)
- **Distributed tracing**: Request flow across services
- **Lineage tracing**: Data flow visualization

### Alerting
- **PagerDuty / Opsgenie** for critical alerts
- **Slack / Teams** for warnings
- **Automated remediation** (restart failed jobs)

---

## 🧪 Data Quality & Testing

### dbt Testing Strategy
```yaml
# models/curated/curated_vendors.yml
version: 2
models:
  - name: curated_vendors
    tests:
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
          max_value: 1000000
    columns:
      - name: vendor_id
        tests:
          - unique
          - not_null
      - name: gst
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
      - name: email
        tests:
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

### Great Expectations
- **Expectation suites** per entity
- **Data profiling** on ingestion
- **Automated DQ reporting**

---

## 🔮 AI-Specific Features

### AI Agent Integration
**Access Methods**:
1. **SQL** (direct query for structured data)
2. **REST API** (standard CRUD)
3. **Vector Search** (semantic similarity)

**AI Data Flagging**:
```sql
curated_invoices:
  - is_ai_generated BOOLEAN
  - ai_confidence_score FLOAT
  - ai_model_version VARCHAR
  - human_verified BOOLEAN
```

### Explainability & Provenance
**Data Provenance Graph**:
```json
{
  "invoice_id": "INV-12345",
  "provenance": {
    "source": "SAP_ECC",
    "extraction_id": "ext-789",
    "transformations": [
      { "step": "dbt_model", "model": "curated_invoices", "version": "v1.2" }
    ],
    "semantic_rules_applied": ["INV_001", "INV_002"],
    "ai_actions": [
      { "agent": "VIM", "action": "VALIDATE", "timestamp": "..." }
    ],
    "lineage": [
      "SAP.BKPF.BELNR → staging_invoices.invoice_no → curated_invoices.invoice_number"
    ]
  }
}
```

**API**: `GET /ai/provenance/{entity}/{id}`

---

## 📈 Scalability & Performance

### Database Optimization
- **Partitioning**: By date (invoices, events)
- **Indexing**: On foreign keys, frequently queried fields
- **Materialized views**: For complex aggregations
- **Connection pooling**: PgBouncer

### Caching Strategy
- **Redis**: API response caching (TTL-based)
- **CDN**: Static metadata (entity definitions)

### Horizontal Scaling
- **Read replicas**: For analytics workloads
- **Sharding**: By tenant (if multi-tenant)

---

## 🔒 Security & Compliance

### Data Encryption
- **At rest**: PostgreSQL TDE (Transparent Data Encryption)
- **In transit**: TLS 1.3
- **Field-level**: AES-256 for sensitive fields

### Compliance Automation
- **GDPR Right to Erasure**: Automated data deletion
- **Data Retention**: Policy-based purging
- **Consent Management**: Opt-in/opt-out tracking

### Penetration Testing
- **Quarterly security audits**
- **Automated vulnerability scanning** (Snyk, Trivy)

---

## 🎯 Success Metrics (KPIs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Data Freshness** | < 5 min lag | Extraction timestamp vs current time |
| **Data Quality Score** | > 95% | Weighted DQ composite |
| **API Latency (p95)** | < 200ms | Prometheus metrics |
| **SAP Sync Success Rate** | > 99.5% | Push/pull success ratio |
| **Lineage Coverage** | 100% | Fields with lineage / total fields |
| **AI Action Accuracy** | > 98% | Human verification rate |
| **Uptime** | 99.9% | Kubernetes health checks |

---

## 📚 Documentation Strategy

### Auto-Generated Docs
- **dbt docs**: Curated layer models
- **OpenAPI/Swagger**: REST API specs
- **OpenMetadata**: Data catalog

### Runbooks
- **Incident response**: SAP connection failures, data quality violations
- **Deployment guide**: Blue-green deployment steps
- **DR plan**: Disaster recovery procedures

---

## 🚧 Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- Multi-schema PostgreSQL setup
- Prisma schema for all layers
- Basic dbt project structure
- Docker + Kubernetes setup

### Phase 2: Semantic Layer (Weeks 3-4)
- Metadata repository
- Business rules engine
- Semantic versioning
- OpenMetadata integration

### Phase 3: Curated Layer (Weeks 5-6)
- dbt transformations
- Data quality framework (Great Expectations)
- SCD Type 2 implementation
- Vector store (pgvector)

### Phase 4: Integration Layer (Weeks 7-8)
- SAP connectors (OData, BAPI)
- Kafka setup
- Event sourcing
- Push/pull workflows

### Phase 5: Governance & APIs (Weeks 9-10)
- RBAC implementation
- Data lineage (OpenLineage)
- REST API development
- Audit trail

### Phase 6: Monitoring & Production (Weeks 11-12)
- Prometheus + Grafana
- ELK stack
- OpenTelemetry
- Load testing & optimization

---

## 🎓 Conclusion

This architecture represents a **production-grade, enterprise-level Data Access Layer** that:

✅ Separates semantic meaning, data preparation, and system integration  
✅ Optimizes for AI consumption and explainability  
✅ Provides full governance, lineage, and compliance  
✅ Supports real-time, bidirectional SAP integration  
✅ Scales horizontally with microservices  
✅ Ensures 99.9% uptime with robust monitoring  

**This is not a POC — this is a deployable enterprise product.**

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-13  
**Owner**: TranAI Data Engineering Team  
**Status**: Approved for Implementation
