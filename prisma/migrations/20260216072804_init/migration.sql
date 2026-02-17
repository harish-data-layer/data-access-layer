-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "audit_layer";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "curated_layer";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "dq_layer";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "event_store";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "integration_layer";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "push_layer";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "semantic_layer";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "vector_layer";

-- CreateTable
CREATE TABLE "semantic_layer"."entities" (
    "id" TEXT NOT NULL,
    "entityId" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "businessDefinition" TEXT NOT NULL,
    "businessOwner" TEXT NOT NULL,
    "dataSteward" TEXT NOT NULL,
    "sourceSystem" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "dataClassification" TEXT NOT NULL,
    "complianceTags" TEXT[],
    "retentionPolicy" TEXT NOT NULL,
    "versionId" TEXT NOT NULL,
    "effectiveFrom" TIMESTAMP(3) NOT NULL,
    "effectiveTo" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "entities_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "semantic_layer"."attributes" (
    "id" TEXT NOT NULL,
    "attributeId" TEXT NOT NULL,
    "entityId" TEXT NOT NULL,
    "attributeName" TEXT NOT NULL,
    "dataType" TEXT NOT NULL,
    "businessDefinition" TEXT NOT NULL,
    "isSensitive" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "attributes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "semantic_layer"."business_rules" (
    "id" TEXT NOT NULL,
    "ruleId" TEXT NOT NULL,
    "ruleName" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "ruleType" TEXT NOT NULL,
    "sqlExpression" TEXT,
    "jsonSchema" JSONB,
    "aiExplanation" TEXT,
    "severity" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdBy" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "business_rules_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "curated_layer"."curated_vendors" (
    "id" TEXT NOT NULL,
    "vendorId" TEXT NOT NULL,
    "vendorCode" TEXT NOT NULL,
    "vendorName" TEXT NOT NULL,
    "gst" TEXT,
    "validFrom" TIMESTAMP(3) NOT NULL,
    "validTo" TIMESTAMP(3),
    "isCurrent" BOOLEAN NOT NULL DEFAULT true,
    "dqScore" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "curated_vendors_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "curated_layer"."curated_invoices" (
    "id" TEXT NOT NULL,
    "invoiceId" TEXT NOT NULL,
    "invoiceNumber" TEXT NOT NULL,
    "vendorId" TEXT NOT NULL,
    "invoiceDate" TIMESTAMP(3) NOT NULL,
    "totalAmount" DOUBLE PRECISION NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'INR',
    "status" TEXT NOT NULL,
    "validFrom" TIMESTAMP(3) NOT NULL,
    "validTo" TIMESTAMP(3),
    "isCurrent" BOOLEAN NOT NULL DEFAULT true,
    "dqScore" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "curated_invoices_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "integration_layer"."extraction_metadata" (
    "id" TEXT NOT NULL,
    "extractionId" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "entity" TEXT NOT NULL,
    "extractionType" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "recordsExtracted" INTEGER NOT NULL DEFAULT 0,
    "recordsFailed" INTEGER NOT NULL DEFAULT 0,
    "startedAt" TIMESTAMP(3) NOT NULL,
    "completedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "extraction_metadata_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "dq_layer"."dq_scores" (
    "id" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "recordId" TEXT,
    "completeness" DOUBLE PRECISION,
    "accuracy" DOUBLE PRECISION,
    "consistency" DOUBLE PRECISION,
    "validity" DOUBLE PRECISION,
    "timeliness" DOUBLE PRECISION,
    "uniqueness" DOUBLE PRECISION,
    "compositeScore" DOUBLE PRECISION NOT NULL,
    "measuredAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "dq_scores_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "event_store"."events" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "eventType" TEXT NOT NULL,
    "aggregateId" TEXT NOT NULL,
    "aggregateType" TEXT NOT NULL,
    "payload" JSONB NOT NULL,
    "metadata" JSONB,
    "correlationId" TEXT,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "version" INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT "events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "audit_layer"."data_access_logs" (
    "id" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "recordId" TEXT,
    "operation" TEXT NOT NULL,
    "accessedBy" TEXT NOT NULL,
    "accessedByType" TEXT NOT NULL,
    "accessedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "data_access_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "audit_layer"."data_change_logs" (
    "id" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "recordId" TEXT NOT NULL,
    "operation" TEXT NOT NULL,
    "oldValue" JSONB,
    "newValue" JSONB,
    "changedBy" TEXT NOT NULL,
    "changedByType" TEXT NOT NULL,
    "changedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "data_change_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "audit_layer"."ai_action_logs" (
    "id" TEXT NOT NULL,
    "actionId" TEXT NOT NULL,
    "agentName" TEXT NOT NULL,
    "actionType" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "recordId" TEXT,
    "inputData" JSONB,
    "outputData" JSONB,
    "confidenceScore" DOUBLE PRECISION,
    "reasoning" TEXT,
    "executedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_action_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "push_layer"."push_queue" (
    "id" TEXT NOT NULL,
    "queueId" TEXT NOT NULL,
    "targetSystem" TEXT NOT NULL,
    "entity" TEXT NOT NULL,
    "operation" TEXT NOT NULL,
    "payload" JSONB NOT NULL,
    "status" TEXT NOT NULL,
    "priority" INTEGER NOT NULL DEFAULT 5,
    "retryCount" INTEGER NOT NULL DEFAULT 0,
    "maxRetries" INTEGER NOT NULL DEFAULT 3,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "processedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),

    CONSTRAINT "push_queue_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "vector_layer"."vendor_embeddings" (
    "id" TEXT NOT NULL,
    "vendorId" TEXT NOT NULL,
    "embedding" TEXT NOT NULL,
    "model" TEXT NOT NULL DEFAULT 'text-embedding-ada-002',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "vendor_embeddings_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "entities_entityId_key" ON "semantic_layer"."entities"("entityId");

-- CreateIndex
CREATE UNIQUE INDEX "attributes_attributeId_key" ON "semantic_layer"."attributes"("attributeId");

-- CreateIndex
CREATE UNIQUE INDEX "business_rules_ruleId_key" ON "semantic_layer"."business_rules"("ruleId");

-- CreateIndex
CREATE UNIQUE INDEX "extraction_metadata_extractionId_key" ON "integration_layer"."extraction_metadata"("extractionId");

-- CreateIndex
CREATE UNIQUE INDEX "events_eventId_key" ON "event_store"."events"("eventId");

-- CreateIndex
CREATE UNIQUE INDEX "ai_action_logs_actionId_key" ON "audit_layer"."ai_action_logs"("actionId");

-- CreateIndex
CREATE UNIQUE INDEX "push_queue_queueId_key" ON "push_layer"."push_queue"("queueId");

-- CreateIndex
CREATE UNIQUE INDEX "vendor_embeddings_vendorId_key" ON "vector_layer"."vendor_embeddings"("vendorId");

-- AddForeignKey
ALTER TABLE "semantic_layer"."attributes" ADD CONSTRAINT "attributes_entityId_fkey" FOREIGN KEY ("entityId") REFERENCES "semantic_layer"."entities"("entityId") ON DELETE RESTRICT ON UPDATE CASCADE;
