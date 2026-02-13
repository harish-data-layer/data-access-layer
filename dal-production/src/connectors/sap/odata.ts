import axios, { AxiosInstance, AxiosError } from 'axios';
import { config } from '../../config';
import { createLogger } from '../../utils/logger';

const logger = createLogger('sap-odata-connector');

export class SapODataClient {
    private client: AxiosInstance;
    private servicePath: string;
    private csrfToken: string | null = null;
    private csrfTokenExpiry: number = 0;

    constructor(servicePath: string = '') {
        this.servicePath = servicePath;
        this.client = axios.create({
            baseURL: `${config.sap.odata.baseUrl}${this.servicePath}`,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'sap-client': config.sap.odata.client,
            },
            auth: {
                username: config.sap.odata.username || '',
                password: config.sap.odata.password || '',
            }
        });

        // Request Interceptor: Logging & CSRF injection
        this.client.interceptors.request.use(async (req) => {
            logger.debug(`[SAP OData Request] ${req.method?.toUpperCase()} ${req.url}`);

            // For write operations, inject CSRF token if available
            if (['post', 'put', 'patch', 'delete'].includes(req.method?.toLowerCase() || '')) {
                if (!this.csrfToken || Date.now() > this.csrfTokenExpiry) {
                    await this.fetchCsrfToken();
                }
                if (this.csrfToken) {
                    req.headers['x-csrf-token'] = this.csrfToken;
                }
            }
            return req;
        });

        // Response Interceptor: Error Handling
        this.client.interceptors.response.use(
            res => res,
            (error: AxiosError) => {
                const sapError = error.response?.data as any;
                const errorMessage = sapError?.error?.message?.value || error.message;

                logger.error(`[SAP OData Error] ${errorMessage}`, {
                    url: error.config?.url,
                    status: error.response?.status,
                    code: sapError?.error?.code
                });
                return Promise.reject(new Error(errorMessage)); // Rethrow specific SAP error
            }
        );
    }

    /**
     * Fetch CSRF Token from SAP Gateway (Required for Write Operations)
     */
    private async fetchCsrfToken(): Promise<void> {
        try {
            const response = await this.client.get('/', {
                headers: { 'x-csrf-token': 'Fetch' }
            });
            const token = response.headers['x-csrf-token'];
            if (token) {
                this.csrfToken = token;
                this.csrfTokenExpiry = Date.now() + (20 * 60 * 1000); // Token valid for ~20 mins typically
                logger.debug('🔑 SAP CSRF Token acquired');
            }
        } catch (error) {
            logger.warn('⚠️ Failed to fetch CSRF token. Write operations may fail.');
        }
    }

    /**
     * Test connectivity to the SAP Gateway service.
     */
    public async checkHealth(): Promise<boolean> {
        try {
            await this.client.get('/$metadata');
            logger.info(`✅ Connected to SAP OData Service: ${this.servicePath}`);
            return true;
        } catch (error) {
            logger.warn(`⚠️ Failed to connect to SAP OData Service: ${this.servicePath}. Is VPN/Tunnel active?`);
            return false;
        }
    }

    /**
     * Execute a GET request with query parameters
     * @param entitySet Name of the EntitySet (e.g., 'A_BusinessPartner')
     * @param params OData query parameters ($filter, $select, $expand, $top, $skip)
     */
    public async read<T>(entitySet: string, params: Record<string, any> = {}): Promise<{ d: { results: T[] } | T, count?: number }> {
        try {
            const response = await this.client.get(`/${entitySet}`, { params });
            return response.data;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Fetch ALL records from an EntitySet, handling server-side pagination (skiptoken).
     * CAUTION: Use with filters to avoid fetching millions of records.
     */
    public async readAll<T>(entitySet: string, params: Record<string, any> = {}): Promise<T[]> {
        let results: T[] = [];
        let nextLink = `/${entitySet}`;
        let queryParams = { ...params };

        // Initial fetch
        // Note: axios params are attached to base URL, but nextLink often contains params too.
        // We need to handle this carefully. For simplicity in this implementation, 
        // we use the 'nextLink' URL returned by SAP directly if available.

        try {
            // First call
            const response = await this.client.get(nextLink, { params: queryParams });
            let data = response.data;

            if (data.d && Array.isArray(data.d.results)) {
                results.push(...data.d.results);

                // Check for generic OData v2 next link structure
                // Adjust property access based on specific SAP version (v2 vs v4)
                let next = data.d.__next;

                while (next) {
                    logger.debug(`[Pagination] Fetching next page...`);
                    // 'next' usually is an absolute URL or relative. We need relative to baseURL.
                    // SAP often returns absolute URL like https://host:port/...
                    // We need to extract the path.
                    const nextUrl = new URL(next);
                    const relativePath = nextUrl.pathname + nextUrl.search;

                    const nextRes = await this.client.get(relativePath);
                    data = nextRes.data;
                    if (data.d && Array.isArray(data.d.results)) {
                        results.push(...data.d.results);
                        next = data.d.__next;
                    } else {
                        next = null;
                    }
                }
            } else if (data.d) {
                // Single object or non-array
                results.push(data.d);
            }

            return results;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Create a new entity in SAP
     * @param entitySet Name of the EntitySet
     * @param payload Data payload
     */
    public async create<T>(entitySet: string, payload: any): Promise<T> {
        const response = await this.client.post(`/${entitySet}`, payload);
        return response.data?.d || response.data;
    }

    /**
     * Update an entity in SAP
     * @param entitySet Name of the EntitySet
     * @param key Entity Key (e.g., "Supplier='1000'")
     * @param payload Data payload to update
     */
    public async update(entitySet: string, key: string, payload: any): Promise<void> {
        // SAP Gateway usually prefers PATCH (MERGE) or PUT
        await this.client.patch(`/${entitySet}(${key})`, payload);
    }
}

// Export pre-configured clients for specific services
export const BusinessPartnerService = new SapODataClient('/API_BUSINESS_PARTNER');
export const SalesOrderService = new SapODataClient('/API_SALES_ORDER_SRV');
