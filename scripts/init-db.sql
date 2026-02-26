-- ============================================
-- TranAI DAL - Database Initialization Script
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schemas for three-layer architecture
CREATE SCHEMA IF NOT EXISTS semantic_layer;
CREATE SCHEMA IF NOT EXISTS curated_layer;
CREATE SCHEMA IF NOT EXISTS integration_layer;
CREATE SCHEMA IF NOT EXISTS dq_layer;
CREATE SCHEMA IF NOT EXISTS vector_layer;
CREATE SCHEMA IF NOT EXISTS event_store;
CREATE SCHEMA IF NOT EXISTS audit_layer;
CREATE SCHEMA IF NOT EXISTS push_layer;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA semantic_layer TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA curated_layer TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA integration_layer TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA dq_layer TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA vector_layer TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA event_store TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA audit_layer TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA push_layer TO postgres;

-- Create helper functions
CREATE OR REPLACE FUNCTION semantic_layer.increment_version(current_version TEXT)
RETURNS TEXT AS $$
DECLARE
    major INT;
    minor INT;
    patch INT;
BEGIN
    -- Parse version (e.g., "v1.2.3")
    major := SUBSTRING(current_version FROM 'v(\d+)\.')::INT;
    minor := SUBSTRING(current_version FROM '\.(\d+)\.')::INT;
    patch := SUBSTRING(current_version FROM '\.(\d+)$')::INT;
    
    -- Increment patch version
    patch := patch + 1;
    
    RETURN 'v' || major || '.' || minor || '.' || patch;
END;
$$ LANGUAGE plpgsql;

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_layer.log_data_change()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_layer."DataChangeLog" (
        "entityName",
        "recordId",
        "operation",
        "oldValue",
        "newValue",
        "changedBy",
        "changedByType",
        "changedAt"
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id::TEXT, OLD.id::TEXT),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        current_user,
        'SYSTEM',
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create DQ score calculation function
CREATE OR REPLACE FUNCTION dq_layer.calculate_composite_score(
    completeness FLOAT,
    accuracy FLOAT,
    consistency FLOAT,
    validity FLOAT,
    timeliness FLOAT,
    uniqueness FLOAT
) RETURNS FLOAT AS $$
BEGIN
    RETURN (
        COALESCE(completeness, 0) * 0.25 +
        COALESCE(accuracy, 0) * 0.25 +
        COALESCE(consistency, 0) * 0.20 +
        COALESCE(validity, 0) * 0.15 +
        COALESCE(timeliness, 0) * 0.10 +
        COALESCE(uniqueness, 0) * 0.05
    );
END;
$$ LANGUAGE plpgsql;

-- Create vector similarity search function
CREATE OR REPLACE FUNCTION vector_layer.search_similar_vendors(
    query_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.8,
    max_results INT DEFAULT 10
) RETURNS TABLE (
    vendor_id TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ve."vendorId",
        1 - (ve.embedding <=> query_embedding) AS similarity
    FROM vector_layer."VendorEmbedding" ve
    WHERE 1 - (ve.embedding <=> query_embedding) > similarity_threshold
    ORDER BY ve.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'TranAI DAL database initialized successfully';
    RAISE NOTICE 'Schemas created: 8';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pgcrypto, vector';
END $$;
