import Redis from 'ioredis';
import { config } from '../config';
import { createLogger } from './logger';
import { cacheHitsTotal, cacheMissesTotal } from './metrics';

const logger = createLogger('redis');

// Redis client singleton
let redisClient: Redis;

export const getRedisClient = (): Redis => {
    if (!redisClient) {
        redisClient = new Redis(config.redis.url, {
            retryStrategy: (times) => {
                const delay = Math.min(times * 50, 2000);
                logger.warn(`Redis connection retry attempt ${times}`, { delay });
                return delay;
            },
            maxRetriesPerRequest: 3,
        });

        redisClient.on('connect', () => {
            logger.info('Redis client connected');
        });

        redisClient.on('error', (error) => {
            logger.error('Redis client error', { error });
        });

        redisClient.on('close', () => {
            logger.warn('Redis client connection closed');
        });
    }

    return redisClient;
};

// Cache helper functions
export class CacheService {
    private client: Redis;
    private defaultTTL: number;

    constructor() {
        this.client = getRedisClient();
        this.defaultTTL = config.redis.ttl;
    }

    async get<T>(key: string): Promise<T | null> {
        try {
            const value = await this.client.get(key);

            if (value) {
                cacheHitsTotal.inc({ cache_type: 'redis' });
                return JSON.parse(value) as T;
            }

            cacheMissesTotal.inc({ cache_type: 'redis' });
            return null;
        } catch (error) {
            logger.error('Cache get error', { key, error });
            return null;
        }
    }

    async set(key: string, value: any, ttl?: number): Promise<void> {
        try {
            const serialized = JSON.stringify(value);
            const expiry = ttl || this.defaultTTL;

            await this.client.setex(key, expiry, serialized);
            logger.debug('Cache set', { key, ttl: expiry });
        } catch (error) {
            logger.error('Cache set error', { key, error });
        }
    }

    async del(key: string): Promise<void> {
        try {
            await this.client.del(key);
            logger.debug('Cache delete', { key });
        } catch (error) {
            logger.error('Cache delete error', { key, error });
        }
    }

    async delPattern(pattern: string): Promise<void> {
        try {
            const keys = await this.client.keys(pattern);
            if (keys.length > 0) {
                await this.client.del(...keys);
                logger.debug('Cache delete pattern', { pattern, count: keys.length });
            }
        } catch (error) {
            logger.error('Cache delete pattern error', { pattern, error });
        }
    }

    async exists(key: string): Promise<boolean> {
        try {
            const result = await this.client.exists(key);
            return result === 1;
        } catch (error) {
            logger.error('Cache exists error', { key, error });
            return false;
        }
    }

    async ttl(key: string): Promise<number> {
        try {
            return await this.client.ttl(key);
        } catch (error) {
            logger.error('Cache TTL error', { key, error });
            return -1;
        }
    }

    async increment(key: string, amount: number = 1): Promise<number> {
        try {
            return await this.client.incrby(key, amount);
        } catch (error) {
            logger.error('Cache increment error', { key, error });
            return 0;
        }
    }

    async decrement(key: string, amount: number = 1): Promise<number> {
        try {
            return await this.client.decrby(key, amount);
        } catch (error) {
            logger.error('Cache decrement error', { key, error });
            return 0;
        }
    }
}

// Export singleton
export const cache = new CacheService();

// Graceful shutdown
export const disconnectRedis = async () => {
    if (redisClient) {
        await redisClient.quit();
        logger.info('Redis client disconnected');
    }
};
