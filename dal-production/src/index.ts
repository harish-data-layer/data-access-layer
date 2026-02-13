import 'dotenv/config';
import { buildServer } from './api/server';
import { config } from './config';
import { logger } from './utils/logger';
import { BusinessPartnerService, SalesOrderService } from './connectors/sap/odata';
import { eventBus } from './connectors/kafka/producer';
import { SapRfcClient } from './connectors/sap/rfc';

async function main() {
    logger.info('🚀 Starting TranAI Data Access Layer (Production Mode)');

    try {
        // 1. Initialize SAP Connectors
        logger.info('🔌 Connecting to SAP Systems...');

        // Connect to Kafka (Background - Non-blocking)
        // This allows the server to start even if Kafka is still initializing
        eventBus.connect().catch((kafkaError) => {
            logger.warn(`⚠️ Kafka Connection Issue: ${kafkaError.message}. Retrying in background...`);
        });

        // Check SAP OData Connectivity (Background)
        BusinessPartnerService.checkHealth().catch(() => { });
        SalesOrderService.checkHealth().catch(() => { });

        // Check RFC Connectivity (Background)
        const rfcClient = new SapRfcClient();
        rfcClient.connect().catch((e) => {
            logger.warn(`⚠️ RFC Connection Failed: ${e.message}. Transactional Posting unavailable.`);
        });

        // 2. Start API Server
        const server = await buildServer();
        const address = await server.listen({
            port: config.port,
            host: '0.0.0.0'
        });

        logger.info(`✅ Server listening on ${address}`);
        logger.info(`✨ Dashboard available at http://localhost:${config.port}`);
        logger.info(`🩺 Health check at http://localhost:${config.port}/health`);

    } catch (err: any) {
        logger.error(`❌ Fatal Error during startup: ${err.message}`);
        process.exit(1);
    }
}

main().catch(err => {
    console.error('Unhandled Startup Error:', err);
    process.exit(1);
});
