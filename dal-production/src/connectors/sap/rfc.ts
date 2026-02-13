import { config } from '../../config';
import { createLogger } from '../../utils/logger';

// Dynamic import for 'node-rfc' to simulate integration
// In a real environment with NWRFC SDK, this would simply be: import { Client } from 'node-rfc'; 
let Client: any;
try {
    // Client = require('node-rfc').Client;
    // Mocking for development environment lacking SAP SDK
    Client = class MockClient {
        constructor(private connectionParams: any) {
            this.connectionParams = connectionParams;
        }

        open() {
            return new Promise<void>((resolve, reject) => {
                // Simulate network latency
                setTimeout(() => {
                    if (config.sap.rfc.ashost === 'mock-sap') {
                        resolve();
                    } else {
                        // In production logic, we would attempt real connection.
                        // For now, let's assume success if configured properly, or fail if missing credentials.
                        if (this.connectionParams.passwd) resolve();
                        else reject(new Error("SAP RFC Error: Lacking credentials for " + this.connectionParams.ashost));
                    }
                }, 500);
            });
        }

        call(bapiName: string, params: any) {
            return new Promise((resolve) => {
                // Simulate BAPI Response
                setTimeout(() => {
                    resolve({
                        RETURN: [{ TYPE: 'S', MESSAGE: 'Successfully posted document via RFC' }],
                        // minimal mock return structure based on BAPI
                    });
                }, 1000);
            });
        }

        close() { return Promise.resolve(); }
    }

} catch (e) {
    createLogger('sap-rfc').warn('node-rfc module not found. Using Mock RFC Client.');
}


const logger = createLogger('sap-rfc-connector');

export class SapRfcClient {
    private client: any; // Type: Client (from node-rfc)

    constructor() {
        this.client = new Client({
            ashost: config.sap.rfc.ashost,
            sysnr: config.sap.rfc.sysnr,
            sysid: config.sap.rfc.sysid,
            user: config.sap.rfc.user,
            passwd: config.sap.rfc.passwd,
            lang: config.sap.rfc.lang,
        });
    }

    public async connect() {
        try {
            logger.info(`Connecting to SAP RFC: ${config.sap.rfc.ashost} (System: ${config.sap.rfc.sysid})`);
            await this.client.open();
            logger.info('✅ SAP RFC Connection Established');
        } catch (error: any) {
            logger.error(`❌ SAP RFC Connection Failed: ${error.message}`);
            throw error; // Propagate up
        }
    }

    public async callBapi(bapiName: string, params: object): Promise<any> {
        try {
            logger.debug(`[RFC EXECUTE] ${bapiName}`, { params });
            const result = await this.client.call(bapiName, params);

            // Check for SAP Return Messages (BAPIRET2 structure)
            if (result.RETURN && Array.isArray(result.RETURN)) {
                const errors = result.RETURN.filter((msg: any) => msg.TYPE === 'E' || msg.TYPE === 'A');
                if (errors.length > 0) {
                    throw new Error(`SAP BAPI Error: ${errors.map((e: any) => e.MESSAGE).join(', ')}`);
                }
            }

            logger.info(`[RFC SUCCESS] ${bapiName}`);
            return result;
        } catch (error: any) {
            logger.error(`[RFC FAIL] ${bapiName}: ${error.message}`);
            throw error;
        }
    }

    public async disconnect() {
        await this.client.close();
    }
}
