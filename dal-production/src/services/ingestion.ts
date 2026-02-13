import { BusinessPartnerService } from '../connectors/sap/odata';
import { eventBus } from '../connectors/kafka/producer';
import { logger } from '../utils/logger';

export class IngestionService {

    /**
     * Trigger a Full Sync of Vendors from S/4HANA
     */
    public async syncVendors(): Promise<{ count: number, status: string, message?: string }> {
        logger.info('[Sync] Starting Vendor Sync from SAP...');

        try {
            // 1. Fetch from SAP OData (Top 10 for demo)
            // In production, we use $skiptoken for pagination
            const response = await BusinessPartnerService.read<any>('A_BusinessPartner', {
                $top: 10,
                $select: 'BusinessPartner,BusinessPartnerFullName,CreationDate'
            });

            let vendors: any[] = [];
            if (response && response.d) {
                if (Array.isArray(response.d.results)) {
                    vendors = response.d.results;
                } else if (Array.isArray(response.d)) {
                    // Some OData v4 returns simple array
                    vendors = response.d;
                } else {
                    vendors = [response.d];
                }
            }

            logger.info(`[Sync] Retrieved ${vendors.length} vendors from SAP S/4HANA`);

            // 2. Publish to Kafka (Event Streaming)
            let publishedCount = 0;
            for (const vendor of vendors) {
                const key = vendor.BusinessPartner || `BP_${Date.now()}_${Math.random()}`;

                const event = {
                    metadata: {
                        source: 'SAP_S4HANA',
                        systemId: 'PRD',
                        entityType: 'Vendor',
                        eventType: 'Changed',
                        timestamp: new Date().toISOString()
                    },
                    data: vendor
                };

                // Producer handles the connection check
                await eventBus.send('sap.vendor.change', key, event);
                publishedCount++;
            }

            logger.info(`[Sync] Published ${publishedCount} events to Kafka topic 'sap.vendor.change'`);
            return { count: publishedCount, status: 'SUCCESS' };

        } catch (error: any) {
            logger.error(`[Sync] Vendor Sync Failed: ${error.message}`);
            // For demo purposes, we don't crash, just report error
            return { count: 0, status: 'ERROR', message: error.message };
        }
    }
}

export const ingestionService = new IngestionService();
