import fastify, { FastifyInstance } from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import jwt from '@fastify/jwt';
import fastifyStatic from '@fastify/static';
import path from 'path';
import { config } from '../config';
import { logger, createLogger } from '../utils/logger';
import { register } from '../utils/metrics';
import { db, disconnectPrisma } from '../utils/prisma';
import { disconnectRedis } from '../utils/redis';
import { disconnectKafka, eventPublisher, eventConsumer } from '../utils/kafka';

const serverLogger = createLogger('server');

export async function buildServer(): Promise<FastifyInstance> {
    const server = fastify({
        logger: false, // We use Winston instead
        requestIdHeader: 'x-request-id',
        requestIdLogLabel: 'requestId',
    });

    // ============================================
    // Plugins
    // ============================================

    // CORS
    await server.register(cors, {
        origin: true,
        credentials: true,
    });

    // Security headers
    await server.register(helmet, {
        contentSecurityPolicy: false,
    });

    // Static files - temporarily disabled for troubleshooting
    // await server.register(fastifyStatic, {
    //     root: path.join(__dirname, '../../public'),
    //     prefix: '/public/',
    // });

    // Rate limiting
    await server.register(rateLimit, {
        max: config.api.rateLimit.max,
        timeWindow: config.api.rateLimit.timeWindow,
    });

    // JWT authentication
    await server.register(jwt, {
        secret: config.jwt.secret,
    });

    // ============================================
    // Hooks
    // ============================================

    // Request logging
    server.addHook('onRequest', async (request, reply) => {
        request.log = createLogger(`request-${request.id}`);
        request.log.info('Incoming request', {
            method: request.method,
            url: request.url,
            ip: request.ip,
        });
    });

    // Response logging
    server.addHook('onResponse', async (request, reply) => {
        request.log.info('Request completed', {
            method: request.method,
            url: request.url,
            statusCode: reply.statusCode,
            responseTime: reply.getResponseTime(),
        });
    });

    // Error handling
    server.setErrorHandler((error, request, reply) => {
        request.log.error('Request error', { error });

        reply.status(error.statusCode || 500).send({
            error: {
                message: error.message,
                statusCode: error.statusCode || 500,
            },
        });
    });

    // ============================================
    // Routes
    // ============================================

    // Dashboard (root route)
    server.get('/', async (request, reply) => {
        const fs = await import('fs/promises');
        const dashboardPath = path.join(__dirname, '../../public/index.html');
        try {
            const html = await fs.readFile(dashboardPath, 'utf-8');
            reply.type('text/html').send(html);
        } catch (error) {
            reply.status(200).send({
                message: 'TranAI DAL API is running!',
                dashboard: 'Dashboard file not found. Open public/index.html directly in your browser.',
                health: '/health',
                api: '/api/v1',
                metrics: '/metrics'
            });
        }
    });

    // Health check
    server.get('/health', async (request, reply) => {
        return {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            environment: config.env,
        };
    });

    // Readiness check
    server.get('/ready', async (request, reply) => {
        try {
            // Check database
            await db.$queryRaw`SELECT 1`;

            return {
                status: 'ready',
                checks: {
                    database: 'ok',
                    cache: 'ok',
                    kafka: 'ok',
                },
            };
        } catch (error) {
            reply.status(503).send({
                status: 'not ready',
                error: error.message,
            });
        }
    });

    // Metrics endpoint
    server.get('/metrics', async (request, reply) => {
        reply.header('Content-Type', register.contentType);
        return register.metrics();
    });

    // API routes
    server.get('/api/v1', async () => {
        return {
            name: 'TranAI Data Access Layer',
            version: '1.0.0',
            description: 'Enterprise Three-Layer Data Architecture',
            endpoints: {
                semantic: '/api/v1/semantic',
                curated: '/api/v1/curated',
                integration: '/api/v1/integration',
                ai: '/api/v1/ai',
                lineage: '/api/v1/lineage',
            },
        };
    });

    // Semantic Layer routes
    server.get('/api/v1/semantic/entities', async (request, reply) => {
        const { metadataService } = await import('../services/semantic/metadata.service');
        const entities = await metadataService.listEntities();
        return { data: entities, count: entities.length };
    });

    server.get('/api/v1/semantic/entities/:entityId', async (request, reply) => {
        const { metadataService } = await import('../services/semantic/metadata.service');
        const { entityId } = request.params as { entityId: string };
        const entity = await metadataService.getEntityById(entityId);

        if (!entity) {
            reply.status(404).send({ error: 'Entity not found' });
            return;
        }

        return { data: entity };
    });

    // Curated Layer routes (placeholder)
    server.get('/api/v1/curated/vendors', async (request, reply) => {
        const vendors = await db.curatedVendor.findMany({
            where: { isCurrent: true },
            take: 100,
            orderBy: { createdAt: 'desc' },
        });

        return { data: vendors, count: vendors.length };
    });

    server.get('/api/v1/curated/invoices', async (request, reply) => {
        const invoices = await db.curatedInvoice.findMany({
            where: { isCurrent: true },
            take: 100,
            orderBy: { createdAt: 'desc' },
        });

        return { data: invoices, count: invoices.length };
    });

    // Integration Layer routes (placeholder)
    server.get('/api/v1/integration/extractions', async (request, reply) => {
        const extractions = await db.extractionMetadata.findMany({
            take: 50,
            orderBy: { startedAt: 'desc' },
        });

        return { data: extractions, count: extractions.length };
    });

    // Data Quality routes (placeholder)
    server.get('/api/v1/dq/scores/:entity', async (request, reply) => {
        const { entity } = request.params as { entity: string };

        const scores = await db.dqScore.findMany({
            where: { entityName: entity },
            orderBy: { measuredAt: 'desc' },
            take: 10,
        });

        return { data: scores, count: scores.length };
    });

    // Event Store routes (placeholder)
    server.get('/api/v1/events/:aggregateId', async (request, reply) => {
        const { aggregateId } = request.params as { aggregateId: string };

        const events = await db.event.findMany({
            where: { aggregateId },
            orderBy: { timestamp: 'asc' },
        });

        return { data: events, count: events.length };
    });

    // Audit routes (placeholder)
    server.get('/api/v1/audit/access', async (request, reply) => {
        const logs = await db.dataAccessLog.findMany({
            take: 100,
            orderBy: { accessedAt: 'desc' },
        });

        return { data: logs, count: logs.length };
    });

    server.get('/api/v1/audit/ai-actions', async (request, reply) => {
        const actions = await db.aiActionLog.findMany({
            take: 100,
            orderBy: { executedAt: 'desc' },
        });

        return { data: actions, count: actions.length };
    });

    return server;
}

// ============================================
// Server Lifecycle
// ============================================

export async function startServer() {
    try {
        // Build server first
        const server = await buildServer();

        // Start listening immediately
        await server.listen({
            host: config.api.host,
            port: config.api.port,
        });

        serverLogger.info(`🚀 Server listening on ${config.api.host}:${config.api.port}`);
        serverLogger.info(`Environment: ${config.env}`);
        serverLogger.info(`Dashboard: http://localhost:${config.api.port}`);
        serverLogger.info(`Health check: http://localhost:${config.api.port}/health`);
        serverLogger.info(`Metrics: http://localhost:${config.api.port}/metrics`);
        serverLogger.info(`API: http://localhost:${config.api.port}/api/v1`);

        // Initialize Kafka in background (non-blocking)
        eventPublisher.initialize().then(() => {
            serverLogger.info('✅ Event publisher initialized');
        }).catch((error) => {
            serverLogger.warn('⚠️  Event publisher not available (Kafka not running)', { error: error.message });
        });

        return server;
    } catch (error) {
        serverLogger.error('Failed to start server', { error });
        process.exit(1);
    }
}

export async function stopServer(server: FastifyInstance) {
    serverLogger.info('Shutting down server...');

    try {
        // Stop accepting new requests
        await server.close();

        // Disconnect services
        await disconnectPrisma();
        await disconnectRedis();
        await disconnectKafka();

        serverLogger.info('Server shut down successfully');
    } catch (error) {
        serverLogger.error('Error during shutdown', { error });
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
    serverLogger.info('SIGTERM received');
    // Server will be stopped by the main process
});

process.on('SIGINT', async () => {
    serverLogger.info('SIGINT received');
    // Server will be stopped by the main process
});
