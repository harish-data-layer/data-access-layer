
// Step-by-Step Execution Log Service

export interface ExecutionLog {
    id: string;
    timestamp: string;
    level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
    component: 'SAP' | 'KAFKA' | 'POSTGRES' | 'AI' | 'DAL';
    message: string;
}

class OrchestrationLogService {
    private logs: ExecutionLog[] = [];

    addLog(component: ExecutionLog['component'], message: string, level: ExecutionLog['level'] = 'INFO') {
        const log: ExecutionLog = {
            id: Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toISOString(),
            level,
            component,
            message
        };
        this.logs.unshift(log);
        if (this.logs.length > 50) this.logs.pop();
        return log;
    }

    getLogs() {
        return this.logs;
    }

    // Simulate a full sync process for "Proof of Work"
    async simulateSyncProcess() {
        this.addLog('DAL', 'Initiating Orchestrated Sync Sequence...', 'INFO');
        await new Promise(r => setTimeout(r, 600));

        this.addLog('SAP', 'Opening RFC Connection to PRD (Client 100)...', 'INFO');
        await new Promise(r => setTimeout(r, 800));

        this.addLog('SAP', 'Executing OData GET /A_BusinessPartner?$top=100', 'INFO');
        await new Promise(r => setTimeout(r, 1200));

        this.addLog('SAP', 'Received 100 records from LFA1. Mapping to Canonical Model.', 'SUCCESS');
        await new Promise(r => setTimeout(r, 500));

        this.addLog('KAFKA', 'Publishing 100 events to topic: sap.vendor.master...', 'INFO');
        await new Promise(r => setTimeout(r, 900));

        this.addLog('POSTGRES', 'Bulk upserting 100 records into table: sap_lfa1', 'INFO');
        await new Promise(r => setTimeout(r, 1100));

        this.addLog('POSTGRES', 'Sync complete. DB Index optimized.', 'SUCCESS');
        this.addLog('DAL', 'Orchestration Finished. 100 Vendors Synced.', 'SUCCESS');
    }
}

export const orchestrationLog = new OrchestrationLogService();
