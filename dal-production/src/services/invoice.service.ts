
import { SapRfcClient } from '../connectors/sap/rfc';
import { logger } from '../utils/logger';
import { SAP_BAPIRET2 } from '../types/sap';

export class InvoiceService {
    private rfcClient: SapRfcClient;

    constructor() {
        this.rfcClient = new SapRfcClient();
    }

    /**
     * Post Incoming Invoice (MIRO) via BAPI
     * BAPI_INCOMINGINVOICE_CREATE
     */
    public async postInvoice(invoiceData: any): Promise<string> {
        logger.info(`[InvoiceService] Posting Invoice ${invoiceData.invoiceNumber} to SAP...`);

        try {
            await this.rfcClient.connect();

            // 1. Prepare BAPI Structures
            const headerData = {
                INVOICE_IND: 'X',
                DOC_TYPE: 'RE',
                DOC_DATE: invoiceData.date,
                PSTNG_DATE: new Date().toISOString().split('T')[0].replace(/-/g, ''), // YYYYMMDD
                REF_DOC_NO: invoiceData.invoiceNumber,
                COMP_CODE: invoiceData.companyCode,
                CURRENCY: invoiceData.currency,
                GROSS_AMOUNT: invoiceData.totalAmount,
                // ... other header fields
            };

            const itemData = invoiceData.items.map((item: any) => ({
                INVOICE_DOC_ITEM: item.lineItem,
                PO_NUMBER: item.poNumber,
                PO_ITEM: item.poItem,
                REF_DOC: item.refDoc, // GR Confirmation
                REF_DOC_YEAR: item.refDocYear,
                REF_DOC_IT: item.refDocItem,
                TAX_CODE: item.taxCode,
                ITEM_AMOUNT: item.amount,
                QUANTITY: item.quantity,
                PO_UNIT: item.unit
            }));

            // 2. Execute BAPI
            logger.debug('[InvoiceService] Calling BAPI_INCOMINGINVOICE_CREATE...');
            const result = await this.rfcClient.callBapi('BAPI_INCOMINGINVOICE_CREATE', {
                HEADERDATA: headerData,
                ITEMDATA: itemData
            });

            // 3. Process Return Messages
            const messages: SAP_BAPIRET2[] = result.RETURN || [];
            const errors = messages.filter(m => m.TYPE === 'E' || m.TYPE === 'A');

            if (errors.length > 0) {
                // Formatting SAP error messages into readable string
                const errorMsg = errors.map(e => `[${e.ID}-${e.NUMBER}] ${e.MESSAGE}`).join('; ');
                throw new Error(`SAP Posting Failed: ${errorMsg}`);
            }

            // Extract Document Number from Success Message or specific return field
            // Usually INVOICEDOCNUMBER in export parameters
            const docNumber = result.INVOICEDOCNUMBER;

            if (!docNumber) {
                throw new Error('SAP did not return an Invoice Document Number despite success message.');
            }

            logger.info(`✅ Invoice Posted. SAP Document: ${docNumber}`);

            // 4. Commit Transaction
            // Critical for SAP BAPIs to persist data
            await this.rfcClient.callBapi('BAPI_TRANSACTION_COMMIT', { WAIT: 'X' });
            logger.info('✅ Transaction Committed.');

            return docNumber;

        } catch (error: any) {
            logger.error(`[InvoiceService] Posting Failed: ${error.message}`);
            // Rollback if connection is still active (optional as SAP often rolls back on disconnect, but good practice)
            try {
                await this.rfcClient.callBapi('BAPI_TRANSACTION_ROLLBACK', {});
            } catch (e) { /* ignore rollback error */ }

            throw error;
        } finally {
            await this.rfcClient.disconnect();
        }
    }
}

export const invoiceService = new InvoiceService();
