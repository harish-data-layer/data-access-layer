
// Mock Database Table Explorer Service

export interface TableRow {
    [key: string]: any;
}

class ExplorerService {
    private tables: Record<string, TableRow[]> = {
        'sap_lfa1': [
            { LIFNR: '0001000120', NAME1: 'Global Logistics Corp', ORT01: 'Berlin', LAND1: 'DE', ERDAT: '2025-01-10' },
            { LIFNR: '0001000155', NAME1: 'Cyberdyne Systems', ORT01: 'San Francisco', LAND1: 'US', ERDAT: '2025-02-01' },
            { LIFNR: '0001000210', NAME1: 'Tyrell Corp', ORT01: 'Tokyo', LAND1: 'JP', ERDAT: '2025-02-15' },
            { LIFNR: '0001000300', NAME1: 'Omni Consumer Products', ORT01: 'Detroit', LAND1: 'US', ERDAT: '2026-01-05' },
            { LIFNR: '0001000450', NAME1: 'Weyland-Yutani', ORT01: 'London', LAND1: 'GB', ERDAT: '2026-02-10' }
        ],
        'sap_rbkp': [
            { BELNR: '5100000001', GJAHR: '2026', BLDAT: '2026-02-10', BUDAT: '2026-02-11', WAERS: 'EUR', HWBAS: 12500.00 },
            { BELNR: '5100000002', GJAHR: '2026', BLDAT: '2026-02-11', BUDAT: '2026-02-12', WAERS: 'USD', HWBAS: 4500.50 },
            { BELNR: '5100000003', GJAHR: '2026', BLDAT: '2026-02-12', BUDAT: '2026-02-12', WAERS: 'GBP', HWBAS: 890.00 }
        ],
        'integration_logs': [
            { id: '1', endpoint: '/sync/vendors', status: 'SUCCESS', duration: '1240ms', records: 100 },
            { id: '2', endpoint: '/invoices/post', status: 'FAILED', error: 'SAP_COMM_FAIL', duration: '450ms', records: 0 }
        ]
    };

    getTableData(tableName: string) {
        return this.tables[tableName] || [];
    }

    getSchema(tableName: string) {
        const data = this.getTableData(tableName);
        if (data.length === 0) return [];
        return Object.keys(data[0]);
    }
}

export const explorerService = new ExplorerService();
