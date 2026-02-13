import { PrismaClient } from '@prisma/client';
import { createLogger } from './logger';
import { dbConnectionsActive, dbQueryDuration } from './metrics';

const logger = createLogger('prisma');

// Prisma client singleton
let prisma: PrismaClient;

export const getPrismaClient = (): PrismaClient => {
    if (!prisma) {
        prisma = new PrismaClient({
            log: [
                { level: 'query', emit: 'event' },
                { level: 'error', emit: 'event' },
                { level: 'warn', emit: 'event' },
            ],
        });

        // Log queries in development
        prisma.$on('query' as never, (e: any) => {
            logger.debug('Query executed', {
                query: e.query,
                params: e.params,
                duration: e.duration,
            });

            // Record metrics
            const table = extractTableName(e.query);
            dbQueryDuration.observe({ operation: 'query', table }, e.duration / 1000);
        });

        // Log errors
        prisma.$on('error' as never, (e: any) => {
            logger.error('Prisma error', { error: e });
        });

        // Log warnings
        prisma.$on('warn' as never, (e: any) => {
            logger.warn('Prisma warning', { warning: e });
        });

        // Track connection pool
        setInterval(() => {
            // This is a placeholder - actual implementation would query Prisma's connection pool
            dbConnectionsActive.set(5); // Default value
        }, 10000);

        logger.info('Prisma client initialized');
    }

    return prisma;
};

// Helper to extract table name from query
const extractTableName = (query: string): string => {
    const match = query.match(/FROM\s+"?(\w+)"?\.?"?(\w+)"?/i);
    return match ? match[2] : 'unknown';
};

// Graceful shutdown
export const disconnectPrisma = async () => {
    if (prisma) {
        await prisma.$disconnect();
        logger.info('Prisma client disconnected');
    }
};

// Export singleton
export const db = getPrismaClient();
