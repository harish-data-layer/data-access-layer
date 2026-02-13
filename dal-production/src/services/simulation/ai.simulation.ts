
// Mock AI Decision Intelligence Service

export interface AIActivity {
    id: string;
    action: string;
    reasoning: string;
    confidence: number;
    timestamp: string;
    status: 'applied' | 'pending' | 'overridden';
}

class AiDecisionService {
    private activities: AIActivity[] = [
        {
            id: 'DEC-8842',
            action: 'Auto-Block Vendor 100045',
            reasoning: 'Abnormal invoice frequency detected (Anomaly Score: 0.92). Potential duplicate billing pattern.',
            confidence: 0.94,
            timestamp: new Date().toISOString(),
            status: 'applied'
        },
        {
            id: 'DEC-8843',
            action: 'Route Invoice #4459 to Senior Auditor',
            reasoning: 'Amount exceeds standard deviation for cost center 4400. Semantic check indicates "IT CAPEX" but GL code is "OPEX".',
            confidence: 0.88,
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            status: 'pending'
        },
        {
            id: 'DEC-8844',
            action: 'Approve Payment Term Exception',
            reasoning: 'Cross-reference with master agreement #A-99 menunjukkan 45 days is valid for this strategic partner.',
            confidence: 0.97,
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            status: 'applied'
        }
    ];

    getActivities() {
        return this.activities;
    }

    getMetrics() {
        return {
            decisionsToday: 145,
            confidenceAvg: 0.91,
            humanOverrides: 2,
            savingsEstimated: '$42,500'
        };
    }
}

export const aiDecisionService = new AiDecisionService();
