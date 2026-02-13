
// Mock SAP Integration Data Generator

class MockSapIntegrationService {
    private connections = [
        { id: 'SAP-PRD-01', name: 'S/4HANA Production', status: 'connected', latency: 120, throughput: 2500 },
        { id: 'SAP-QA-02', name: 'S/4HANA QA', status: 'connected', latency: 45, throughput: 120 },
        { id: 'SAP-ECC-legacy', name: 'ECC 6.0 (Legacy)', status: 'degraded', latency: 300, throughput: 45 }
    ];

    private syncHistory = [
        { id: 101, pipeline: 'Vendor Master', status: 'success', duration: '12s', records: 1200 },
        { id: 102, pipeline: 'Invoices (Daily)', status: 'processing', duration: '2m', records: 450 },
        { id: 103, pipeline: 'Material Master', status: 'failed', duration: '5s', error: 'RFC_CONNECTION_TIMEOUT' }
    ];

    getSystemStatus() {
        // Randomly fluctuate latency and throughput
        this.connections.forEach(conn => {
            conn.latency = Math.max(10, conn.latency + (Math.random() < 0.5 ? -10 : 10));
            conn.throughput = Math.max(0, conn.throughput + (Math.random() < 0.5 ? -50 : 50));
            if (Math.random() > 0.95) conn.status = Math.random() > 0.5 ? 'connected' : 'degraded';
        });
        return this.connections;
    }

    getPipelineStatus() {
        return this.syncHistory;
    }

    triggerPipeline(pipelineId: string) {
        return { status: 'triggered', jobId: `JOB-${Date.now()}` };
    }
}

export const mockSapService = new MockSapIntegrationService();
