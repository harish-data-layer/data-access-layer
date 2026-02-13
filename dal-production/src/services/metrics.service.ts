
// Mock Global Metrics
const mockGlobalMetrics = {
    recordsSynced: 1254320,
    apiCalls: 45210,
    lastSyncDuration: 120,
    activePipelines: 12,
    failedJobs: 0
};

export const metricsService = {
    getOverview: async () => {
        // In real impl, query Prisma or Prometheus here
        return {
            sapConnections: 3,
            recordsSynced: mockGlobalMetrics.recordsSynced,
            apiCalls: mockGlobalMetrics.apiCalls,
            uptime: 99.98,
            activePipelines: mockGlobalMetrics.activePipelines,
            failedJobs: mockGlobalMetrics.failedJobs
        };
    },

    incrementSync: (count: number) => {
        mockGlobalMetrics.recordsSynced += count;
    },

    incrementApiCalls: () => {
        mockGlobalMetrics.apiCalls++;
    }
};
