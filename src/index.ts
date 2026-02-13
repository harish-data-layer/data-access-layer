import { startServer, stopServer } from './api/server';
import { logger } from './utils/logger';

async function main() {
    logger.info('🚀 Starting TranAI Data Access Layer...');
    logger.info('================================================');

    try {
        const server = await startServer();

        // Graceful shutdown
        const shutdown = async (signal: string) => {
            logger.info(`${signal} received, shutting down gracefully...`);
            await stopServer(server);
            process.exit(0);
        };

        process.on('SIGTERM', () => shutdown('SIGTERM'));
        process.on('SIGINT', () => shutdown('SIGINT'));

    } catch (error) {
        logger.error('Fatal error during startup', { error });
        process.exit(1);
    }
}

main();
