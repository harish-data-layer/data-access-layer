
import { BusinessPartnerService } from '../connectors/sap/odata';
import { eventBus } from '../connectors/kafka/producer';
import { logger } from '../utils/logger';
import { SAP_LFA1 } from '../types/sap';

export class VendorService {

    /**
     * Sync Vendors from SAP S/4HANA
     * Supports Delta Sync if lastSyncTime is provided.
     */
    public async syncVendors(lastSyncTime?: Date): Promise<number> {
        logger.info(`[VendorService] Starting Sync... Last Sync: ${lastSyncTime || 'NEVER'}`);

        try {
            // Build OData Filter
            const filters: string[] = [];
            if (lastSyncTime) {
                // OData format: 2023-10-27T10:00:00Z
                // Standard SAP OData often uses 'LastChangeDate' or 'ChangedOn'
                filters.push(`LastChangeDate ge datetime'${lastSyncTime.toISOString()}'`);
            }

            const query: any = {
                $top: 100, // Batch size
                $select: 'BusinessPartner,BusinessPartnerFullName,CreationDate,LastChangeDate,AddressID'
            };

            if (filters.length > 0) {
                query.$filter = filters.join(' and ');
            }

            // Fetch Data (using the new readAll for pagination)
            // Note: In real world, we map the OData result to SAP_LFA1 structure
            const sapVendors = await BusinessPartnerService.readAll<any>('A_BusinessPartner', query);

            if (sapVendors.length === 0) {
                logger.info('[VendorService] No changes found.');
                return 0;
            }

            logger.info(`[VendorService] Found ${sapVendors.length} updated vendors.`);

            // Publish Events
            let count = 0;
            for (const sapVendor of sapVendors) {
                const standardizedVendor = this.mapToCanonical(sapVendor);

                await eventBus.send('sap.vendor.change', standardizedVendor.vendorId, {
                    metadata: {
                        source: 'SAP_S/4',
                        entity: 'Vendor',
                        timestamp: new Date().toISOString()
                    },
                    data: standardizedVendor
                });
                count++;
            }

            return count;

        } catch (error: any) {
            logger.error(`[VendorService] Sync Failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Map SAP S/4HANA OData structure to DAL Canonical Model
     */
    private mapToCanonical(sapData: any) {
        return {
            vendorId: sapData.BusinessPartner, // LFA1-LIFNR
            name: sapData.BusinessPartnerFullName, // LFA1-NAME1
            createdAt: sapData.CreationDate, // LFA1-ERDAT
            lastModified: sapData.LastChangeDate,
            addressId: sapData.AddressID
        };
    }
}

export const vendorService = new VendorService();
