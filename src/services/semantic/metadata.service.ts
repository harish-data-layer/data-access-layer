import { db } from '../../utils/prisma';
import { createLogger } from '../../utils/logger';
import { cache } from '../../utils/redis';
import { Entity, Attribute } from '@prisma/client';

const logger = createLogger('metadata-service');

export interface CreateEntityDto {
    entityName: string;
    businessDefinition: string;
    businessOwner: string;
    dataSteward: string;
    sourceSystem: string;
    domain: string;
    dataClassification: string;
    complianceTags: string[];
    retentionPolicy: string;
    legalBasis?: string;
    sensitivityLevel?: string;
    aiReasoningScope?: string;
    embeddingNamespace?: string;
    ontologyMapping?: any;
    featureHints?: any;
}

export interface CreateAttributeDto {
    entityId: string;
    attributeName: string;
    dataType: string;
    businessDefinition: string;
    isSensitive?: boolean;
    maskingRule?: string;
    encryptionMethod?: string;
    validationRules?: any;
    aiContext?: string;
    defaultValue?: string;
    isNullable?: boolean;
}

export class MetadataService {
    // ============================================
    // Entity Management
    // ============================================

    async createEntity(data: CreateEntityDto): Promise<Entity> {
        logger.info('Creating entity', { entityName: data.entityName });

        const entity = await db.entity.create({
            data: {
                ...data,
                versionId: 'v1.0.0',
                effectiveFrom: new Date(),
                effectiveTo: null,
            },
        });

        // Invalidate cache
        await cache.delPattern(`entity:*`);

        logger.info('Entity created', { entityId: entity.entityId });
        return entity;
    }

    async getEntityByName(entityName: string): Promise<Entity | null> {
        const cacheKey = `entity:name:${entityName}`;

        // Try cache first
        const cached = await cache.get<Entity>(cacheKey);
        if (cached) {
            return cached;
        }

        // Query database
        const entity = await db.entity.findFirst({
            where: {
                entityName,
                effectiveTo: null, // Current version only
            },
            include: {
                attributes: true,
            },
        });

        if (entity) {
            await cache.set(cacheKey, entity, 3600); // Cache for 1 hour
        }

        return entity;
    }

    async getEntityById(entityId: string): Promise<Entity | null> {
        const cacheKey = `entity:id:${entityId}`;

        const cached = await cache.get<Entity>(cacheKey);
        if (cached) {
            return cached;
        }

        const entity = await db.entity.findUnique({
            where: { entityId },
            include: {
                attributes: true,
            },
        });

        if (entity) {
            await cache.set(cacheKey, entity, 3600);
        }

        return entity;
    }

    async listEntities(filters?: {
        domain?: string;
        dataClassification?: string;
        sourceSystem?: string;
    }): Promise<Entity[]> {
        const where: any = {
            effectiveTo: null, // Current versions only
        };

        if (filters?.domain) {
            where.domain = filters.domain;
        }

        if (filters?.dataClassification) {
            where.dataClassification = filters.dataClassification;
        }

        if (filters?.sourceSystem) {
            where.sourceSystem = filters.sourceSystem;
        }

        return db.entity.findMany({
            where,
            include: {
                attributes: true,
            },
            orderBy: {
                entityName: 'asc',
            },
        });
    }

    async updateEntity(entityId: string, updates: Partial<CreateEntityDto>): Promise<Entity> {
        logger.info('Updating entity', { entityId });

        // Get current version
        const current = await db.entity.findFirst({
            where: { entityId, effectiveTo: null },
        });

        if (!current) {
            throw new Error(`Entity not found: ${entityId}`);
        }

        // Close current version
        await db.entity.updateMany({
            where: { entityId, effectiveTo: null },
            data: { effectiveTo: new Date() },
        });

        // Create new version
        const newVersion = this.incrementVersion(current.versionId);

        const entity = await db.entity.create({
            data: {
                ...current,
                ...updates,
                id: undefined, // Let Prisma generate new ID
                versionId: newVersion,
                effectiveFrom: new Date(),
                effectiveTo: null,
            },
        });

        // Invalidate cache
        await cache.delPattern(`entity:*`);

        logger.info('Entity updated', { entityId, newVersion });
        return entity;
    }

    async getEntityVersions(entityId: string): Promise<Entity[]> {
        return db.entity.findMany({
            where: { entityId },
            orderBy: { effectiveFrom: 'desc' },
        });
    }

    // ============================================
    // Attribute Management
    // ============================================

    async createAttribute(data: CreateAttributeDto): Promise<Attribute> {
        logger.info('Creating attribute', {
            entityId: data.entityId,
            attributeName: data.attributeName,
        });

        const attribute = await db.attribute.create({
            data,
        });

        // Invalidate entity cache
        await cache.delPattern(`entity:*`);

        logger.info('Attribute created', { attributeId: attribute.attributeId });
        return attribute;
    }

    async getAttributesByEntity(entityId: string): Promise<Attribute[]> {
        return db.attribute.findMany({
            where: { entityId },
            orderBy: { attributeName: 'asc' },
        });
    }

    async updateAttribute(
        attributeId: string,
        updates: Partial<CreateAttributeDto>
    ): Promise<Attribute> {
        logger.info('Updating attribute', { attributeId });

        const attribute = await db.attribute.update({
            where: { attributeId },
            data: updates,
        });

        // Invalidate cache
        await cache.delPattern(`entity:*`);

        logger.info('Attribute updated', { attributeId });
        return attribute;
    }

    async deleteAttribute(attributeId: string): Promise<void> {
        logger.info('Deleting attribute', { attributeId });

        await db.attribute.delete({
            where: { attributeId },
        });

        // Invalidate cache
        await cache.delPattern(`entity:*`);

        logger.info('Attribute deleted', { attributeId });
    }

    // ============================================
    // Helper Methods
    // ============================================

    private incrementVersion(currentVersion: string): string {
        // Parse version (e.g., "v1.2.3")
        const match = currentVersion.match(/v(\d+)\.(\d+)\.(\d+)/);
        if (!match) {
            return 'v1.0.1';
        }

        const [, major, minor, patch] = match;
        const newPatch = parseInt(patch) + 1;

        return `v${major}.${minor}.${newPatch}`;
    }

    // ============================================
    // Search & Discovery
    // ============================================

    async searchEntities(query: string): Promise<Entity[]> {
        return db.entity.findMany({
            where: {
                effectiveTo: null,
                OR: [
                    { entityName: { contains: query, mode: 'insensitive' } },
                    { businessDefinition: { contains: query, mode: 'insensitive' } },
                    { domain: { contains: query, mode: 'insensitive' } },
                ],
            },
            include: {
                attributes: true,
            },
            take: 20,
        });
    }

    async getEntitiesByCompliance(complianceTag: string): Promise<Entity[]> {
        return db.entity.findMany({
            where: {
                effectiveTo: null,
                complianceTags: {
                    has: complianceTag,
                },
            },
            include: {
                attributes: true,
            },
        });
    }

    async getSensitiveEntities(): Promise<Entity[]> {
        return db.entity.findMany({
            where: {
                effectiveTo: null,
                dataClassification: {
                    in: ['Confidential', 'Restricted', 'PII'],
                },
            },
            include: {
                attributes: true,
            },
        });
    }
}

export const metadataService = new MetadataService();
