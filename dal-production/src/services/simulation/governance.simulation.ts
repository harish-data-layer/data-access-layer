
// Mock Governance & Risk Service

export interface RiskAlert {
    id: string;
    level: 'critical' | 'warning' | 'info';
    category: string;
    message: string;
    timestamp: string;
}

class GovernanceService {
    private alerts: RiskAlert[] = [
        {
            id: 'GS-001',
            level: 'critical',
            category: 'Data Privacy',
            message: 'Unmasked PII detected in SAP extraction (Topic: sap.vendor.master.raw)',
            timestamp: new Date().toISOString()
        },
        {
            id: 'GS-002',
            level: 'warning',
            category: 'Compliance',
            message: 'Incomplete Audit Trail for User ADM_BATCH on S/4HANA System PRD',
            timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString()
        },
        {
            id: 'GS-003',
            level: 'info',
            category: 'Governance',
            message: 'New data classification policy applied to 14 datasets',
            timestamp: new Date(Date.now() - 2 * 3600000).toISOString()
        }
    ];

    getAlerts() {
        return this.alerts;
    }

    getHealthScore() {
        return {
            overall: 94,
            trend: '+1.2%',
            violationsToday: 2,
            unmaskedFields: 4
        };
    }
}

export const governanceService = new GovernanceService();
