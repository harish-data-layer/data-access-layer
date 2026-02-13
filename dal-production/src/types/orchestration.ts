
export interface SAPSystem {
    id: string;
    name: string;
    host: string;
    status: 'connected' | 'degraded' | 'disconnected';
    latency: number;
    activeJobs: number;
}

export interface PipelineStep {
    timestamp: string;
    message: string;
    component: string;
}

export interface PipelineJob {
    id: string;
    entityId: string;
    status: 'running' | 'success' | 'failed' | 'pending';
    progress: number;
    startTime: string;
    endTime?: string;
    steps: PipelineStep[];
    error?: string;
}

export interface DataEntity {
    id: string;
    name: string;
    table: string;
    recordCount: number;
    lastSync: string;
    health: number;
}
