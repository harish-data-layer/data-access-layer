import { Registry, Counter, Histogram, Gauge } from 'prom-client';
import { config } from '../config';

// Create registry
export const register = new Registry();

// Default labels
register.setDefaultLabels({
    app: 'tranai-dal',
    env: config.env,
});

// HTTP Metrics
export const httpRequestDuration = new Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'route', 'status_code'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
    registers: [register],
});

export const httpRequestTotal = new Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status_code'],
    registers: [register],
});

// Database Metrics
export const dbQueryDuration = new Histogram({
    name: 'db_query_duration_seconds',
    help: 'Duration of database queries in seconds',
    labelNames: ['operation', 'table'],
    buckets: [0.001, 0.01, 0.05, 0.1, 0.5, 1],
    registers: [register],
});

export const dbConnectionsActive = new Gauge({
    name: 'db_connections_active',
    help: 'Number of active database connections',
    registers: [register],
});

// Data Quality Metrics
export const dqScoreGauge = new Gauge({
    name: 'data_quality_score',
    help: 'Data quality composite score',
    labelNames: ['entity', 'dimension'],
    registers: [register],
});

export const dqViolationsTotal = new Counter({
    name: 'dq_violations_total',
    help: 'Total number of data quality violations',
    labelNames: ['entity', 'severity'],
    registers: [register],
});

// SAP Integration Metrics
export const sapSyncTotal = new Counter({
    name: 'sap_sync_total',
    help: 'Total SAP sync operations',
    labelNames: ['source', 'entity', 'status'],
    registers: [register],
});

export const sapSyncDuration = new Histogram({
    name: 'sap_sync_duration_seconds',
    help: 'Duration of SAP sync operations',
    labelNames: ['source', 'entity'],
    buckets: [1, 5, 10, 30, 60, 120],
    registers: [register],
});

export const sapPushQueueSize = new Gauge({
    name: 'sap_push_queue_size',
    help: 'Number of items in SAP push queue',
    labelNames: ['status'],
    registers: [register],
});

// Event Store Metrics
export const eventsPublished = new Counter({
    name: 'events_published_total',
    help: 'Total number of events published',
    labelNames: ['event_type'],
    registers: [register],
});

export const eventsProcessed = new Counter({
    name: 'events_processed_total',
    help: 'Total number of events processed',
    labelNames: ['event_type', 'status'],
    registers: [register],
});

// AI Metrics
export const aiActionsTotal = new Counter({
    name: 'ai_actions_total',
    help: 'Total number of AI actions',
    labelNames: ['agent', 'action_type', 'status'],
    registers: [register],
});

export const aiConfidenceScore = new Histogram({
    name: 'ai_confidence_score',
    help: 'AI confidence scores',
    labelNames: ['agent', 'entity'],
    buckets: [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99],
    registers: [register],
});

// Cache Metrics
export const cacheHitsTotal = new Counter({
    name: 'cache_hits_total',
    help: 'Total number of cache hits',
    labelNames: ['cache_type'],
    registers: [register],
});

export const cacheMissesTotal = new Counter({
    name: 'cache_misses_total',
    help: 'Total number of cache misses',
    labelNames: ['cache_type'],
    registers: [register],
});

// Lineage Metrics
export const lineageTracked = new Counter({
    name: 'lineage_tracked_total',
    help: 'Total number of lineage entries tracked',
    labelNames: ['source_entity', 'target_entity'],
    registers: [register],
});

// Helper functions
export const recordHttpRequest = (
    method: string,
    route: string,
    statusCode: number,
    duration: number
) => {
    httpRequestDuration.observe({ method, route, status_code: statusCode }, duration);
    httpRequestTotal.inc({ method, route, status_code: statusCode });
};

export const recordDbQuery = (operation: string, table: string, duration: number) => {
    dbQueryDuration.observe({ operation, table }, duration);
};

export const recordDqScore = (entity: string, dimension: string, score: number) => {
    dqScoreGauge.set({ entity, dimension }, score);
};

export const recordSapSync = (
    source: string,
    entity: string,
    status: 'success' | 'failure',
    duration: number
) => {
    sapSyncTotal.inc({ source, entity, status });
    sapSyncDuration.observe({ source, entity }, duration);
};

export const recordAiAction = (
    agent: string,
    actionType: string,
    status: 'success' | 'failure',
    confidenceScore?: number
) => {
    aiActionsTotal.inc({ agent, action_type: actionType, status });
    if (confidenceScore !== undefined) {
        aiConfidenceScore.observe({ agent, entity: actionType }, confidenceScore);
    }
};
