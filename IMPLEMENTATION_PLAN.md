# 🚀 TranAI DAL - Implementation Plan

## 📋 Overview

This document provides a **step-by-step implementation plan** for building the enterprise-grade Three-Layer Data Access Layer. Each phase includes specific tasks, deliverables, and acceptance criteria.

---

## 🎯 Implementation Strategy

### Approach
- **Incremental delivery**: Each phase produces working, testable components
- **Vertical slices**: Build end-to-end functionality per entity (Vendor → Invoice → PO)
- **Test-driven**: Write tests before implementation
- **Documentation-first**: Update docs as code evolves

### Timeline
**Total Duration**: 12 weeks (3 months)

---

## 📅 Phase 1: Foundation & Infrastructure (Weeks 1-2)

### Objectives
- Set up multi-schema PostgreSQL database
- Configure Prisma for all three layers
- Establish Docker + Kubernetes environment
- Set up CI/CD pipeline

### Tasks

#### 1.1 Database Setup
```bash
# Create PostgreSQL database with multiple schemas
CREATE DATABASE tranai_dal;

\c tranai_dal

-- Layer schemas
CREATE SCHEMA semantic_layer;
CREATE SCHEMA curated_layer;
CREATE SCHEMA integration_layer;
CREATE SCHEMA dq_layer;
CREATE SCHEMA vector_layer;
CREATE SCHEMA event_store;
CREATE SCHEMA audit_layer;
CREATE SCHEMA push_layer;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector"; -- for pgvector
```

**Deliverable**: Multi-schema database with extensions

#### 1.2 Prisma Schema Design
**File**: `prisma/schema.prisma`

```prisma
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["multiSchema"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  schemas  = [
    "semantic_layer",
    "curated_layer", 
    "integration_layer",
    "dq_layer",
    "vector_layer",
    "event_store",
    "audit_layer",
    "push_layer"
  ]
}

// SEMANTIC LAYER
model Entity {
  id                   Int       @id @default(autoincrement())
  entityId             String    @unique @default(uuid())
  entityName           String
  businessDefinition   String
  businessOwner        String
  dataSteward          String
  sourceSystem         String
  domain               String
  dataClassification   String
  complianceTags       String[]
  retentionPolicy      String
  versionId            String
  effectiveFrom        DateTime
  effectiveTo          DateTime?
  aiReasoningScope     String?
  embeddingNamespace   String?
  createdAt            DateTime  @default(now())
  updatedAt            DateTime  @updatedAt
  
  attributes           Attribute[]
  
  @@schema("semantic_layer")
}

model Attribute {
  id                   Int       @id @default(autoincrement())
  attributeId          String    @unique @default(uuid())
  entityId             String
  entity               Entity    @relation(fields: [entityId], references: [entityId])
  attributeName        String
  dataType             String
  businessDefinition   String
  isSensitive          Boolean   @default(false)
  maskingRule          String?
  validationRules      Json?
  aiContext            String?
  
  @@schema("semantic_layer")
}

model BusinessRule {
  id                   Int       @id @default(autoincrement())
  ruleId               String    @unique @default(uuid())
  ruleName             String
  entityName           String
  ruleType             String    // VALIDATION, TRANSFORMATION, CONSTRAINT
  sqlExpression        String?
  jsonSchema           Json?
  aiExplanation        String?
  severity             String    // ERROR, WARNING, INFO
  isActive             Boolean   @default(true)
  
  @@schema("semantic_layer")
}

model LineageMap {
  id                   Int       @id @default(autoincrement())
  sourceSystem         String
  sourceEntity         String
  sourceField          String
  curatedEntity        String
  curatedField         String
  transformationLogic  String?
  
  @@schema("semantic_layer")
}

// CURATED LAYER
model CuratedVendor {
  id                   Int       @id @default(autoincrement())
  vendorId             String    @unique @default(uuid())
  vendorCode           String?
  name                 String
  gst                  String
  email                String
  phone                String?
  address              String?
  city                 String?
  state                String?
  country              String?
  postalCode           String?
  bankName             String?
  bankAccount          String?   // Encrypted
  ifscCode             String?
  paymentTerms         String?
  currency             String?
  status               String?
  riskScore            Float?
  dqScore              Float?
  isAiGenerated        Boolean   @default(false)
  aiConfidenceScore    Float?
  aiModelVersion       String?
  humanVerified        Boolean   @default(false)
  validFrom            DateTime  @default(now())
  validTo              DateTime?
  isCurrent            Boolean   @default(true)
  createdAt            DateTime  @default(now())
  updatedAt            DateTime  @updatedAt
  
  invoices             CuratedInvoice[]
  purchaseOrders       CuratedPurchaseOrder[]
  
  @@schema("curated_layer")
}

model CuratedPurchaseOrder {
  id                   Int       @id @default(autoincrement())
  poId                 String    @unique @default(uuid())
  poNumber             String
  vendorId             String
  vendor               CuratedVendor @relation(fields: [vendorId], references: [vendorId])
  amount               Float
  currency             String?
  status               String?
  poDate               DateTime?
  deliveryDate         DateTime?
  paymentTerms         String?
  createdBy            String?
  approvedBy           String?
  department           String?
  costCenter           String?
  taxAmount            Float?
  totalAmount          Float?
  notes                String?
  dqScore              Float?
  isAiGenerated        Boolean   @default(false)
  validFrom            DateTime  @default(now())
  validTo              DateTime?
  isCurrent            Boolean   @default(true)
  createdAt            DateTime  @default(now())
  updatedAt            DateTime  @updatedAt
  
  @@schema("curated_layer")
}

model CuratedInvoice {
  id                   Int       @id @default(autoincrement())
  invoiceId            String    @unique @default(uuid())
  invoiceNo            String
  vendorId             String
  vendor               CuratedVendor @relation(fields: [vendorId], references: [vendorId])
  poNumber             String?
  amount               Float
  taxAmount            Float?
  totalAmount          Float?
  currency             String?
  status               String?
  invoiceDate          DateTime?
  dueDate              DateTime?
  paymentDate          DateTime?
  paymentMethod        String?
  createdBy            String?
  approvedBy           String?
  notes                String?
  agingDays            Int?
  dqScore              Float?
  isAiGenerated        Boolean   @default(false)
  aiConfidenceScore    Float?
  humanVerified        Boolean   @default(false)
  validFrom            DateTime  @default(now())
  validTo              DateTime?
  isCurrent            Boolean   @default(true)
  createdAt            DateTime  @default(now())
  updatedAt            DateTime  @updatedAt
  
  @@schema("curated_layer")
}

// DATA QUALITY LAYER
model DqScore {
  id                   Int       @id @default(autoincrement())
  entityName           String
  recordId             String?
  columnName           String?
  completeness         Float?
  accuracy             Float?
  consistency          Float?
  validity             Float?
  timeliness           Float?
  uniqueness           Float?
  compositeScore       Float
  measuredAt           DateTime  @default(now())
  
  @@schema("dq_layer")
}

model DqViolation {
  id                   Int       @id @default(autoincrement())
  ruleId               String
  entityName           String
  recordId             String
  columnName           String?
  violationType        String
  expectedValue        String?
  actualValue          String?
  severity             String
  detectedAt           DateTime  @default(now())
  resolvedAt           DateTime?
  
  @@schema("dq_layer")
}

// INTEGRATION LAYER
model StagingVendor {
  id                   Int       @id @default(autoincrement())
  extractionId         String
  rawData              Json
  sourceSystem         String
  extractedAt          DateTime  @default(now())
  processedAt          DateTime?
  status               String    @default("PENDING")
  
  @@schema("integration_layer")
}

model ExtractionMetadata {
  id                   Int       @id @default(autoincrement())
  extractionId         String    @unique @default(uuid())
  sourceSystem         String
  entityName           String
  extractionType       String    // FULL, INCREMENTAL
  lastSyncTimestamp    DateTime?
  recordsExtracted     Int?
  recordsLoaded        Int?
  status               String
  errorLog             String?
  startedAt            DateTime  @default(now())
  completedAt          DateTime?
  
  @@schema("integration_layer")
}

// PUSH LAYER
model PushQueue {
  id                   Int       @id @default(autoincrement())
  pushId               String    @unique @default(uuid())
  targetSystem         String
  entityName           String
  operation            String    // CREATE, UPDATE, DELETE
  payload              Json
  priority             Int       @default(5)
  requiresApproval     Boolean   @default(false)
  approvedBy           String?
  approvedAt           DateTime?
  status               String    @default("PENDING")
  retryCount           Int       @default(0)
  maxRetries           Int       @default(3)
  errorLog             String?
  createdAt            DateTime  @default(now())
  scheduledAt          DateTime?
  executedAt           DateTime?
  
  @@schema("push_layer")
}

// EVENT STORE
model Event {
  id                   Int       @id @default(autoincrement())
  eventId              String    @unique @default(uuid())
  eventType            String
  aggregateId          String
  timestamp            DateTime  @default(now())
  actor                String
  payloadFull          Json
  payloadDelta         Json?
  correlationId        String?
  metadata             Json?
  
  @@index([aggregateId])
  @@index([eventType])
  @@schema("event_store")
}

// AUDIT LAYER
model DataAccessLog {
  id                   Int       @id @default(autoincrement())
  userId               String
  userRole             String
  entityName           String
  recordId             String?
  operation            String    // READ, WRITE, DELETE
  accessedAt           DateTime  @default(now())
  ipAddress            String?
  
  @@schema("audit_layer")
}

model AiActionLog {
  id                   Int       @id @default(autoincrement())
  actionId             String    @unique @default(uuid())
  agentName            String
  actionType           String
  entityName           String
  recordId             String?
  confidenceScore      Float?
  reasoning            String?
  humanVerified        Boolean   @default(false)
  executedAt           DateTime  @default(now())
  
  @@schema("audit_layer")
}

// VECTOR LAYER
model VendorEmbedding {
  id                   Int       @id @default(autoincrement())
  vendorId             String    @unique
  embedding            Unsupported("vector(1536)")?
  textContent          String
  modelVersion         String
  createdAt            DateTime  @default(now())
  
  @@schema("vector_layer")
}
```

**Deliverable**: Complete Prisma schema for all layers

#### 1.3 Environment Configuration
**File**: `.env`

```env
# Database
DATABASE_URL="postgresql://postgres:password@localhost:5432/tranai_dal?schema=public"

# Kafka
KAFKA_BROKERS="localhost:9092"
KAFKA_CLIENT_ID="tranai-dal"

# SAP
SAP_HOST="sap.example.com"
SAP_CLIENT="100"
SAP_USER="SAPUSER"
SAP_PASSWORD="encrypted"

# Redis
REDIS_URL="redis://localhost:6379"

# Vault
VAULT_ADDR="http://localhost:8200"
VAULT_TOKEN="dev-token"

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"

# API
API_PORT=3000
API_RATE_LIMIT=100

# Environment
NODE_ENV="development"
```

#### 1.4 Docker Compose Setup
**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: tranai_dal
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  vault:
    image: hashicorp/vault:latest
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: dev-token
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    cap_add:
      - IPC_LOCK

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

**Deliverable**: Working Docker Compose environment

#### 1.5 Project Structure
```
dal-setup/
├── .env
├── .gitignore
├── docker-compose.yml
├── package.json
├── tsconfig.json
├── ARCHITECTURE.md
├── IMPLEMENTATION_PLAN.md
├── prisma/
│   ├── schema.prisma
│   └── migrations/
├── src/
│   ├── services/
│   │   ├── semantic/
│   │   ├── curated/
│   │   ├── integration/
│   │   └── ai/
│   ├── api/
│   │   ├── routes/
│   │   └── middleware/
│   ├── utils/
│   ├── config/
│   └── types/
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── curated/
│   │   └── semantic/
│   ├── tests/
│   └── dbt_project.yml
├── python/
│   ├── sap_connectors/
│   ├── data_quality/
│   └── requirements.txt
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
├── kubernetes/
│   ├── deployments/
│   ├── services/
│   └── ingress/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

**Deliverable**: Complete project structure

### Acceptance Criteria
- [ ] PostgreSQL running with all schemas created
- [ ] Prisma schema compiles without errors
- [ ] Docker Compose brings up all services
- [ ] Can connect to all services (DB, Kafka, Redis, Vault)
- [ ] Project structure follows best practices

---

## 📅 Phase 2: Semantic Layer (Weeks 3-4)

### Objectives
- Build metadata repository
- Implement business rules engine
- Set up semantic versioning
- Integrate OpenMetadata

### Tasks

#### 2.1 Metadata Repository Service
**File**: `src/services/semantic/metadata.service.ts`

```typescript
import { PrismaClient } from '@prisma/client';

export class MetadataService {
  private prisma = new PrismaClient();

  async createEntity(data: CreateEntityDto) {
    return this.prisma.entity.create({
      data: {
        ...data,
        effectiveFrom: new Date(),
        versionId: 'v1.0.0',
      },
    });
  }

  async getEntityByName(entityName: string) {
    return this.prisma.entity.findFirst({
      where: {
        entityName,
        effectiveTo: null, // Current version
      },
      include: {
        attributes: true,
      },
    });
  }

  async createNewVersion(entityId: string, updates: Partial<Entity>) {
    // Close current version
    await this.prisma.entity.updateMany({
      where: { entityId, effectiveTo: null },
      data: { effectiveTo: new Date() },
    });

    // Create new version
    const current = await this.prisma.entity.findFirst({
      where: { entityId },
      orderBy: { effectiveFrom: 'desc' },
    });

    const newVersion = incrementVersion(current.versionId);

    return this.prisma.entity.create({
      data: {
        ...current,
        ...updates,
        versionId: newVersion,
        effectiveFrom: new Date(),
        effectiveTo: null,
      },
    });
  }

  async getLineage(entityName: string, fieldName: string) {
    return this.prisma.lineageMap.findMany({
      where: {
        OR: [
          { curatedEntity: entityName, curatedField: fieldName },
          { sourceEntity: entityName, sourceField: fieldName },
        ],
      },
    });
  }
}
```

#### 2.2 Business Rules Engine
**File**: `src/services/semantic/rules.service.ts`

```typescript
export class RulesService {
  async validateRecord(entityName: string, record: any) {
    const rules = await this.prisma.businessRule.findMany({
      where: { entityName, isActive: true },
    });

    const violations = [];

    for (const rule of rules) {
      const isValid = await this.executeRule(rule, record);
      if (!isValid) {
        violations.push({
          ruleId: rule.ruleId,
          ruleName: rule.ruleName,
          severity: rule.severity,
          explanation: rule.aiExplanation,
        });
      }
    }

    return violations;
  }

  private async executeRule(rule: BusinessRule, record: any) {
    switch (rule.ruleType) {
      case 'VALIDATION':
        return this.executeSqlRule(rule.sqlExpression, record);
      case 'JSON_SCHEMA':
        return this.executeJsonSchemaRule(rule.jsonSchema, record);
      default:
        return true;
    }
  }
}
```

#### 2.3 OpenMetadata Integration
**File**: `src/services/semantic/openmetadata.service.ts`

```typescript
import { MetadataClient } from '@open-metadata/client';

export class OpenMetadataService {
  private client: MetadataClient;

  async syncEntity(entity: Entity) {
    await this.client.createOrUpdateTable({
      name: entity.entityName,
      description: entity.businessDefinition,
      owner: entity.businessOwner,
      tags: entity.complianceTags,
      columns: entity.attributes.map(attr => ({
        name: attr.attributeName,
        dataType: attr.dataType,
        description: attr.businessDefinition,
      })),
    });
  }
}
```

### Acceptance Criteria
- [ ] Can create and version entities
- [ ] Business rules execute correctly
- [ ] Lineage tracking works
- [ ] OpenMetadata syncs metadata

---

## 📅 Phase 3: Curated Layer (Weeks 5-6)

### Objectives
- Build dbt transformation models
- Implement data quality framework
- Set up SCD Type 2
- Configure pgvector for embeddings

### Tasks

#### 3.1 dbt Project Setup
**File**: `dbt/dbt_project.yml`

```yaml
name: 'tranai_dal'
version: '1.0.0'
config-version: 2

profile: 'tranai'

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

models:
  tranai_dal:
    staging:
      +materialized: view
      +schema: integration_layer
    curated:
      +materialized: table
      +schema: curated_layer
```

#### 3.2 dbt Models
**File**: `dbt/models/curated/curated_vendors.sql`

```sql
{{
  config(
    materialized='incremental',
    unique_key='vendor_id',
    on_schema_change='append_new_columns'
  )
}}

WITH source AS (
  SELECT * FROM {{ ref('staging_vendors') }}
  {% if is_incremental() %}
  WHERE extracted_at > (SELECT MAX(updated_at) FROM {{ this }})
  {% endif %}
),

transformed AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['vendor_code']) }} AS vendor_id,
    vendor_code,
    TRIM(UPPER(name)) AS name,
    UPPER(gst) AS gst,
    LOWER(email) AS email,
    phone,
    address,
    city,
    state,
    country,
    postal_code,
    bank_name,
    {{ encrypt_field('bank_account') }} AS bank_account,
    ifsc_code,
    payment_terms,
    currency,
    status,
    CURRENT_TIMESTAMP AS valid_from,
    NULL AS valid_to,
    TRUE AS is_current,
    FALSE AS is_ai_generated,
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
  FROM source
)

SELECT * FROM transformed
```

#### 3.3 Data Quality with Great Expectations
**File**: `python/data_quality/expectations.py`

```python
import great_expectations as gx

context = gx.get_context()

# Create expectation suite
suite = context.add_expectation_suite("vendor_quality")

# Add expectations
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="vendor_code")
)

suite.add_expectation(
    gx.expectations.ExpectColumnValuesToMatchRegex(
        column="gst",
        regex=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    )
)

suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeUnique(column="vendor_id")
)

# Run validation
checkpoint = context.add_checkpoint(
    name="vendor_checkpoint",
    validations=[
        {
            "batch_request": {
                "datasource_name": "postgres",
                "data_asset_name": "curated_vendors",
            },
            "expectation_suite_name": "vendor_quality",
        }
    ],
)

result = checkpoint.run()
```

#### 3.4 SCD Type 2 Implementation
**File**: `dbt/macros/scd_type2.sql`

```sql
{% macro scd_type2(source_table, target_table, unique_key, updated_at_field) %}

MERGE INTO {{ target_table }} AS target
USING {{ source_table }} AS source
ON target.{{ unique_key }} = source.{{ unique_key }}
  AND target.is_current = TRUE

WHEN MATCHED AND source.{{ updated_at_field }} > target.updated_at THEN
  UPDATE SET
    valid_to = CURRENT_TIMESTAMP,
    is_current = FALSE

WHEN NOT MATCHED THEN
  INSERT ({{ unique_key }}, ..., valid_from, is_current)
  VALUES (source.{{ unique_key }}, ..., CURRENT_TIMESTAMP, TRUE);

-- Insert new versions
INSERT INTO {{ target_table }} ({{ unique_key }}, ..., valid_from, is_current)
SELECT {{ unique_key }}, ..., CURRENT_TIMESTAMP, TRUE
FROM {{ source_table }}
WHERE {{ unique_key }} IN (
  SELECT {{ unique_key }}
  FROM {{ target_table }}
  WHERE valid_to = CURRENT_TIMESTAMP
);

{% endmacro %}
```

### Acceptance Criteria
- [ ] dbt models run successfully
- [ ] Data quality tests pass
- [ ] SCD Type 2 tracks history correctly
- [ ] Embeddings stored in pgvector

---

## 📅 Phase 4: Integration Layer (Weeks 7-8)

### Objectives
- Build SAP connectors (OData, BAPI)
- Set up Kafka event streaming
- Implement event sourcing
- Create push/pull workflows

### Tasks

#### 4.1 SAP OData Connector
**File**: `python/sap_connectors/odata_client.py`

```python
import httpx
from typing import Dict, List

class SAPODataClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = (username, password)
        self.client = httpx.AsyncClient(auth=self.auth)

    async def get_vendors(self, filter_params: Dict = None) -> List[Dict]:
        url = f"{self.base_url}/sap/opu/odata/sap/MD_VENDOR_SRV/VendorSet"
        
        params = {}
        if filter_params:
            params['$filter'] = self._build_filter(filter_params)
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        return response.json()['d']['results']

    async def create_invoice(self, invoice_data: Dict) -> Dict:
        url = f"{self.base_url}/sap/opu/odata/sap/FI_INVOICE_SRV/InvoiceSet"
        
        response = await self.client.post(url, json=invoice_data)
        response.raise_for_status()
        
        return response.json()['d']
```

#### 4.2 Kafka Producer/Consumer
**File**: `src/services/integration/kafka.service.ts`

```typescript
import { Kafka, Producer, Consumer } from 'kafkajs';

export class KafkaService {
  private kafka: Kafka;
  private producer: Producer;
  private consumer: Consumer;

  constructor() {
    this.kafka = new Kafka({
      clientId: process.env.KAFKA_CLIENT_ID,
      brokers: process.env.KAFKA_BROKERS.split(','),
    });

    this.producer = this.kafka.producer();
    this.consumer = this.kafka.consumer({ groupId: 'dal-consumer' });
  }

  async publishEvent(topic: string, event: any) {
    await this.producer.send({
      topic,
      messages: [
        {
          key: event.eventId,
          value: JSON.stringify(event),
          headers: {
            'event-type': event.eventType,
            'correlation-id': event.correlationId,
          },
        },
      ],
    });
  }

  async consumeEvents(topic: string, handler: (event: any) => Promise<void>) {
    await this.consumer.subscribe({ topic, fromBeginning: false });

    await this.consumer.run({
      eachMessage: async ({ message }) => {
        const event = JSON.parse(message.value.toString());
        await handler(event);
      },
    });
  }
}
```

#### 4.3 Event Sourcing
**File**: `src/services/integration/event-store.service.ts`

```typescript
export class EventStoreService {
  async appendEvent(event: CreateEventDto) {
    const storedEvent = await this.prisma.event.create({
      data: {
        eventType: event.eventType,
        aggregateId: event.aggregateId,
        actor: event.actor,
        payloadFull: event.payload,
        payloadDelta: event.delta,
        correlationId: event.correlationId,
        metadata: event.metadata,
      },
    });

    // Publish to Kafka
    await this.kafkaService.publishEvent('events', storedEvent);

    return storedEvent;
  }

  async getEventStream(aggregateId: string) {
    return this.prisma.event.findMany({
      where: { aggregateId },
      orderBy: { timestamp: 'asc' },
    });
  }

  async replayEvents(aggregateId: string, toTimestamp?: Date) {
    const events = await this.getEventStream(aggregateId);
    
    let state = {};
    for (const event of events) {
      if (toTimestamp && event.timestamp > toTimestamp) break;
      state = this.applyEvent(state, event);
    }

    return state;
  }
}
```

#### 4.4 Push Queue Service
**File**: `src/services/integration/push-queue.service.ts`

```typescript
export class PushQueueService {
  async enqueuePush(data: CreatePushDto) {
    return this.prisma.pushQueue.create({
      data: {
        targetSystem: data.targetSystem,
        entityName: data.entityName,
        operation: data.operation,
        payload: data.payload,
        requiresApproval: data.requiresApproval,
        priority: data.priority || 5,
      },
    });
  }

  async processPushQueue() {
    const pendingPushes = await this.prisma.pushQueue.findMany({
      where: {
        status: 'PENDING',
        OR: [
          { requiresApproval: false },
          { AND: [{ requiresApproval: true }, { approvedAt: { not: null } }] },
        ],
      },
      orderBy: [{ priority: 'asc' }, { createdAt: 'asc' }],
      take: 10,
    });

    for (const push of pendingPushes) {
      await this.executePush(push);
    }
  }

  private async executePush(push: PushQueue) {
    try {
      // Execute SAP push
      const result = await this.sapService.push(push.targetSystem, push.payload);

      await this.prisma.pushQueue.update({
        where: { id: push.id },
        data: {
          status: 'SUCCESS',
          executedAt: new Date(),
        },
      });

      // Log event
      await this.eventStoreService.appendEvent({
        eventType: 'PUSH_SUCCESS',
        aggregateId: push.pushId,
        actor: 'SYSTEM',
        payload: result,
      });
    } catch (error) {
      await this.handlePushError(push, error);
    }
  }

  private async handlePushError(push: PushQueue, error: Error) {
    const newRetryCount = push.retryCount + 1;

    if (newRetryCount >= push.maxRetries) {
      // Move to DLQ
      await this.prisma.pushQueue.update({
        where: { id: push.id },
        data: {
          status: 'FAILED',
          errorLog: error.message,
          retryCount: newRetryCount,
        },
      });
    } else {
      // Retry with exponential backoff
      const backoffMs = Math.pow(2, newRetryCount) * 1000;
      await this.prisma.pushQueue.update({
        where: { id: push.id },
        data: {
          retryCount: newRetryCount,
          scheduledAt: new Date(Date.now() + backoffMs),
        },
      });
    }
  }
}
```

### Acceptance Criteria
- [ ] Can pull data from SAP via OData
- [ ] Kafka publishes and consumes events
- [ ] Event sourcing tracks all changes
- [ ] Push queue processes with retries

---

## 📅 Phase 5: Governance & APIs (Weeks 9-10)

### Objectives
- Implement RBAC
- Build data lineage tracking
- Create REST APIs
- Set up audit logging

### Tasks

#### 5.1 RBAC Middleware
**File**: `src/api/middleware/rbac.middleware.ts`

```typescript
export const rbacMiddleware = (requiredPermissions: string[]) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user; // From JWT
    const userPermissions = await getUserPermissions(user.role);

    const hasPermission = requiredPermissions.every(perm =>
      userPermissions.includes(perm)
    );

    if (!hasPermission) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    next();
  };
};

// Usage
router.get(
  '/curated/vendors',
  authenticate,
  rbacMiddleware(['curated:read']),
  vendorController.list
);
```

#### 5.2 Lineage API
**File**: `src/api/routes/lineage.routes.ts`

```typescript
router.get('/lineage/:entity/:field', async (req, res) => {
  const { entity, field } = req.params;

  const lineage = await lineageService.getFieldLineage(entity, field);

  res.json({
    entity,
    field,
    lineage: {
      upstream: lineage.upstream, // Source systems
      downstream: lineage.downstream, // Consuming systems
      transformations: lineage.transformations,
    },
  });
});
```

#### 5.3 REST API Routes
**File**: `src/api/routes/index.ts`

```typescript
// Semantic Layer
app.use('/api/v1/semantic', semanticRoutes);

// Curated Layer
app.use('/api/v1/curated', curatedRoutes);

// Integration Layer
app.use('/api/v1/integration', integrationRoutes);

// AI Layer
app.use('/api/v1/ai', aiRoutes);

// Lineage
app.use('/api/v1/lineage', lineageRoutes);
```

#### 5.4 Audit Logging
**File**: `src/api/middleware/audit.middleware.ts`

```typescript
export const auditMiddleware = async (req: Request, res: Response, next: NextFunction) => {
  const startTime = Date.now();

  res.on('finish', async () => {
    await prisma.dataAccessLog.create({
      data: {
        userId: req.user?.id || 'anonymous',
        userRole: req.user?.role || 'guest',
        entityName: req.params.entity || 'unknown',
        operation: req.method,
        accessedAt: new Date(),
        ipAddress: req.ip,
      },
    });
  });

  next();
};
```

### Acceptance Criteria
- [ ] RBAC enforces permissions
- [ ] Lineage API returns correct data
- [ ] All APIs documented with OpenAPI
- [ ] Audit logs capture all access

---

## 📅 Phase 6: Monitoring & Production (Weeks 11-12)

### Objectives
- Set up Prometheus + Grafana
- Configure ELK stack
- Implement OpenTelemetry
- Load testing & optimization

### Tasks

#### 6.1 Prometheus Metrics
**File**: `src/utils/metrics.ts`

```typescript
import { Registry, Counter, Histogram } from 'prom-client';

export const register = new Registry();

export const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register],
});

export const dqScoreGauge = new Gauge({
  name: 'data_quality_score',
  help: 'Data quality composite score',
  labelNames: ['entity'],
  registers: [register],
});

export const sapSyncCounter = new Counter({
  name: 'sap_sync_total',
  help: 'Total SAP sync operations',
  labelNames: ['source', 'status'],
  registers: [register],
});
```

#### 6.2 OpenTelemetry Tracing
**File**: `src/utils/tracing.ts`

```typescript
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { PrismaInstrumentation } from '@prisma/instrumentation';

const provider = new NodeTracerProvider();
provider.register();

registerInstrumentations({
  instrumentations: [
    new HttpInstrumentation(),
    new PrismaInstrumentation(),
  ],
});
```

#### 6.3 Grafana Dashboards
**File**: `monitoring/grafana/dashboards/dal-overview.json`

```json
{
  "dashboard": {
    "title": "TranAI DAL Overview",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Data Quality Score",
        "targets": [
          {
            "expr": "avg(data_quality_score) by (entity)"
          }
        ]
      },
      {
        "title": "SAP Sync Status",
        "targets": [
          {
            "expr": "sap_sync_total"
          }
        ]
      }
    ]
  }
}
```

#### 6.4 Load Testing
**File**: `tests/load/k6-script.js`

```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  let res = http.get('http://localhost:3000/api/v1/curated/vendors');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
}
```

### Acceptance Criteria
- [ ] Prometheus scrapes metrics
- [ ] Grafana dashboards visualize data
- [ ] OpenTelemetry traces requests
- [ ] Load tests pass (p95 < 200ms)

---

## 🎯 Final Deliverables

### Code Deliverables
- [ ] Complete Prisma schema with migrations
- [ ] All microservices (Semantic, Curated, Integration, AI)
- [ ] dbt transformation models
- [ ] SAP connectors (Python)
- [ ] REST APIs with OpenAPI docs
- [ ] Kafka event streaming
- [ ] RBAC & audit logging
- [ ] Data quality framework
- [ ] Monitoring & observability

### Documentation Deliverables
- [ ] Architecture document (ARCHITECTURE.md)
- [ ] Implementation plan (this document)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] dbt documentation
- [ ] Runbooks (deployment, incident response)
- [ ] User guides

### Infrastructure Deliverables
- [ ] Docker Compose for local dev
- [ ] Kubernetes manifests for production
- [ ] Terraform scripts for cloud deployment
- [ ] CI/CD pipelines (GitHub Actions)

---

## 🚀 Deployment Checklist

### Pre-Production
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Load tests meet SLA (p95 < 200ms)
- [ ] Security scan (no critical vulnerabilities)
- [ ] Data quality tests pass
- [ ] Lineage validated
- [ ] RBAC tested

### Production Deployment
- [ ] Blue-green deployment configured
- [ ] Health checks enabled
- [ ] Monitoring dashboards live
- [ ] Alerting rules configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan tested
- [ ] Runbooks reviewed

### Post-Deployment
- [ ] Smoke tests pass
- [ ] Metrics baseline established
- [ ] On-call rotation defined
- [ ] Stakeholder training completed

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Latency (p95) | < 200ms | Prometheus |
| Data Quality Score | > 95% | DQ framework |
| SAP Sync Success Rate | > 99.5% | Event logs |
| Uptime | 99.9% | Kubernetes |
| Lineage Coverage | 100% | Metadata scan |

---

## 🎓 Conclusion

This implementation plan provides a **comprehensive, phased approach** to building the enterprise-grade TranAI Data Access Layer. Each phase builds on the previous one, ensuring incremental delivery of value while maintaining production quality.

**Estimated Effort**: 12 weeks (3 months) with a team of 3-4 engineers.

**Next Steps**: Begin Phase 1 - Foundation & Infrastructure.

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-13  
**Owner**: TranAI Engineering Team  
**Status**: Ready for Implementation
