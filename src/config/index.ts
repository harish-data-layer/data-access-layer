import dotenv from 'dotenv';
import { z } from 'zod';

// Load environment variables
dotenv.config();

// Environment schema validation
const envSchema = z.object({
    // Environment
    NODE_ENV: z.enum(['development', 'staging', 'production']).default('development'),
    LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),

    // Database
    DATABASE_URL: z.string().url(),
    DB_POOL_MIN: z.string().transform(Number).default('2'),
    DB_POOL_MAX: z.string().transform(Number).default('10'),

    // API
    API_HOST: z.string().default('0.0.0.0'),
    API_PORT: z.string().transform(Number).default('3000'),
    API_RATE_LIMIT: z.string().transform(Number).default('100'),
    API_RATE_WINDOW: z.string().transform(Number).default('60000'),

    // JWT
    JWT_SECRET: z.string().min(32),
    JWT_EXPIRY: z.string().default('24h'),

    // Kafka
    KAFKA_BROKERS: z.string(),
    KAFKA_CLIENT_ID: z.string().default('tranai-dal'),
    KAFKA_GROUP_ID: z.string().default('tranai-dal-consumer'),
    KAFKA_TOPICS_EVENTS: z.string().default('dal.events'),
    KAFKA_TOPICS_PUSH: z.string().default('dal.push'),
    KAFKA_TOPICS_PULL: z.string().default('dal.pull'),

    // Redis
    REDIS_URL: z.string().url(),
    REDIS_TTL: z.string().transform(Number).default('3600'),

    // Vault
    VAULT_ADDR: z.string().url(),
    VAULT_TOKEN: z.string(),
    VAULT_NAMESPACE: z.string().default('tranai'),

    // SAP
    SAP_HOST: z.string(),
    SAP_PORT: z.string().transform(Number).default('443'),
    SAP_CLIENT: z.string(),
    SAP_USER: z.string(),
    SAP_PASSWORD: z.string(),
    SAP_ODATA_BASE_URL: z.string().url(),

    // OpenTelemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: z.string().url(),
    OTEL_SERVICE_NAME: z.string().default('tranai-dal'),
    OTEL_TRACES_SAMPLER: z.string().default('always_on'),

    // Prometheus
    PROMETHEUS_PORT: z.string().transform(Number).default('9090'),
    METRICS_ENABLED: z.string().transform(v => v === 'true').default('true'),

    // Data Quality
    DQ_THRESHOLD_COMPLETENESS: z.string().transform(Number).default('0.95'),
    DQ_THRESHOLD_ACCURACY: z.string().transform(Number).default('0.98'),
    DQ_THRESHOLD_CONSISTENCY: z.string().transform(Number).default('0.95'),
    DQ_THRESHOLD_VALIDITY: z.string().transform(Number).default('0.99'),
    DQ_THRESHOLD_TIMELINESS: z.string().transform(Number).default('0.90'),
    DQ_THRESHOLD_UNIQUENESS: z.string().transform(Number).default('0.99'),

    // Vector
    VECTOR_DIMENSION: z.string().transform(Number).default('1536'),
    VECTOR_SIMILARITY_THRESHOLD: z.string().transform(Number).default('0.8'),

    // Audit
    AUDIT_RETENTION_DAYS: z.string().transform(Number).default('2555'),
    AUDIT_LOG_ALL_READS: z.string().transform(v => v === 'true').default('false'),
    AUDIT_LOG_ALL_WRITES: z.string().transform(v => v === 'true').default('true'),

    // Feature Flags
    FEATURE_SEMANTIC_VERSIONING: z.string().transform(v => v === 'true').default('true'),
    FEATURE_EVENT_SOURCING: z.string().transform(v => v === 'true').default('true'),
    FEATURE_PUSH_APPROVAL: z.string().transform(v => v === 'true').default('true'),
    FEATURE_AI_EMBEDDINGS: z.string().transform(v => v === 'true').default('true'),

    // OpenMetadata
    OPENMETADATA_URL: z.string().url().optional(),
    OPENMETADATA_TOKEN: z.string().optional(),

    // Backup
    BACKUP_ENABLED: z.string().transform(v => v === 'true').default('true'),
    BACKUP_SCHEDULE: z.string().default('0 2 * * *'),
    BACKUP_RETENTION_DAYS: z.string().transform(Number).default('30'),
});

// Parse and validate environment variables
const env = envSchema.parse(process.env);

// Export configuration
export const config = {
    env: env.NODE_ENV,
    isDevelopment: env.NODE_ENV === 'development',
    isProduction: env.NODE_ENV === 'production',
    logLevel: env.LOG_LEVEL,

    database: {
        url: env.DATABASE_URL,
        pool: {
            min: env.DB_POOL_MIN,
            max: env.DB_POOL_MAX,
        },
    },

    api: {
        host: env.API_HOST,
        port: env.API_PORT,
        rateLimit: {
            max: env.API_RATE_LIMIT,
            timeWindow: env.API_RATE_WINDOW,
        },
    },

    jwt: {
        secret: env.JWT_SECRET,
        expiry: env.JWT_EXPIRY,
    },

    kafka: {
        brokers: env.KAFKA_BROKERS.split(','),
        clientId: env.KAFKA_CLIENT_ID,
        groupId: env.KAFKA_GROUP_ID,
        topics: {
            events: env.KAFKA_TOPICS_EVENTS,
            push: env.KAFKA_TOPICS_PUSH,
            pull: env.KAFKA_TOPICS_PULL,
        },
    },

    redis: {
        url: env.REDIS_URL,
        ttl: env.REDIS_TTL,
    },

    vault: {
        address: env.VAULT_ADDR,
        token: env.VAULT_TOKEN,
        namespace: env.VAULT_NAMESPACE,
    },

    sap: {
        host: env.SAP_HOST,
        port: env.SAP_PORT,
        client: env.SAP_CLIENT,
        user: env.SAP_USER,
        password: env.SAP_PASSWORD,
        odataBaseUrl: env.SAP_ODATA_BASE_URL,
    },

    telemetry: {
        endpoint: env.OTEL_EXPORTER_OTLP_ENDPOINT,
        serviceName: env.OTEL_SERVICE_NAME,
        sampler: env.OTEL_TRACES_SAMPLER,
    },

    prometheus: {
        port: env.PROMETHEUS_PORT,
        enabled: env.METRICS_ENABLED,
    },

    dataQuality: {
        thresholds: {
            completeness: env.DQ_THRESHOLD_COMPLETENESS,
            accuracy: env.DQ_THRESHOLD_ACCURACY,
            consistency: env.DQ_THRESHOLD_CONSISTENCY,
            validity: env.DQ_THRESHOLD_VALIDITY,
            timeliness: env.DQ_THRESHOLD_TIMELINESS,
            uniqueness: env.DQ_THRESHOLD_UNIQUENESS,
        },
    },

    vector: {
        dimension: env.VECTOR_DIMENSION,
        similarityThreshold: env.VECTOR_SIMILARITY_THRESHOLD,
    },

    audit: {
        retentionDays: env.AUDIT_RETENTION_DAYS,
        logAllReads: env.AUDIT_LOG_ALL_READS,
        logAllWrites: env.AUDIT_LOG_ALL_WRITES,
    },

    features: {
        semanticVersioning: env.FEATURE_SEMANTIC_VERSIONING,
        eventSourcing: env.FEATURE_EVENT_SOURCING,
        pushApproval: env.FEATURE_PUSH_APPROVAL,
        aiEmbeddings: env.FEATURE_AI_EMBEDDINGS,
    },

    openMetadata: {
        url: env.OPENMETADATA_URL,
        token: env.OPENMETADATA_TOKEN,
    },

    backup: {
        enabled: env.BACKUP_ENABLED,
        schedule: env.BACKUP_SCHEDULE,
        retentionDays: env.BACKUP_RETENTION_DAYS,
    },
} as const;

export type Config = typeof config;
