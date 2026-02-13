import { db } from '../../utils/prisma';
import { createLogger } from '../../utils/logger';
import { BusinessRule } from '@prisma/client';
import Ajv from 'ajv';

const logger = createLogger('rules-service');
const ajv = new Ajv();

export interface CreateBusinessRuleDto {
    ruleName: string;
    entityName: string;
    ruleType: 'VALIDATION' | 'TRANSFORMATION' | 'CONSTRAINT';
    sqlExpression?: string;
    jsonSchema?: any;
    aiExplanation?: string;
    severity: 'ERROR' | 'WARNING' | 'INFO';
    createdBy: string;
    approvedBy?: string;
}

export interface RuleViolation {
    ruleId: string;
    ruleName: string;
    severity: string;
    explanation: string;
    field?: string;
    expectedValue?: any;
    actualValue?: any;
}

export class BusinessRulesService {
    // ============================================
    // Rule Management
    // ============================================

    async createRule(data: CreateBusinessRuleDto): Promise<BusinessRule> {
        logger.info('Creating business rule', { ruleName: data.ruleName });

        const rule = await db.businessRule.create({
            data: {
                ...data,
                isActive: true,
            },
        });

        logger.info('Business rule created', { ruleId: rule.ruleId });
        return rule;
    }

    async getRuleById(ruleId: string): Promise<BusinessRule | null> {
        return db.businessRule.findUnique({
            where: { ruleId },
        });
    }

    async getRulesByEntity(entityName: string, activeOnly: boolean = true): Promise<BusinessRule[]> {
        const where: any = { entityName };
        if (activeOnly) {
            where.isActive = true;
        }

        return db.businessRule.findMany({
            where,
            orderBy: { createdAt: 'desc' },
        });
    }

    async updateRule(ruleId: string, updates: Partial<CreateBusinessRuleDto>): Promise<BusinessRule> {
        logger.info('Updating business rule', { ruleId });

        const rule = await db.businessRule.update({
            where: { ruleId },
            data: updates,
        });

        logger.info('Business rule updated', { ruleId });
        return rule;
    }

    async deactivateRule(ruleId: string): Promise<void> {
        logger.info('Deactivating business rule', { ruleId });

        await db.businessRule.update({
            where: { ruleId },
            data: { isActive: false },
        });

        logger.info('Business rule deactivated', { ruleId });
    }

    async activateRule(ruleId: string): Promise<void> {
        logger.info('Activating business rule', { ruleId });

        await db.businessRule.update({
            where: { ruleId },
            data: { isActive: true },
        });

        logger.info('Business rule activated', { ruleId });
    }

    // ============================================
    // Rule Validation
    // ============================================

    async validateRecord(entityName: string, record: any): Promise<RuleViolation[]> {
        const rules = await this.getRulesByEntity(entityName, true);
        const violations: RuleViolation[] = [];

        for (const rule of rules) {
            const violation = await this.executeRule(rule, record);
            if (violation) {
                violations.push(violation);
            }
        }

        if (violations.length > 0) {
            logger.warn('Rule violations detected', {
                entityName,
                violationCount: violations.length,
            });
        }

        return violations;
    }

    private async executeRule(rule: BusinessRule, record: any): Promise<RuleViolation | null> {
        try {
            switch (rule.ruleType) {
                case 'VALIDATION':
                    return await this.executeValidationRule(rule, record);
                case 'TRANSFORMATION':
                    return await this.executeTransformationRule(rule, record);
                case 'CONSTRAINT':
                    return await this.executeConstraintRule(rule, record);
                default:
                    logger.warn('Unknown rule type', { ruleType: rule.ruleType });
                    return null;
            }
        } catch (error) {
            logger.error('Rule execution failed', { ruleId: rule.ruleId, error });
            return {
                ruleId: rule.ruleId,
                ruleName: rule.ruleName,
                severity: 'ERROR',
                explanation: `Rule execution failed: ${error}`,
            };
        }
    }

    private async executeValidationRule(
        rule: BusinessRule,
        record: any
    ): Promise<RuleViolation | null> {
        // JSON Schema validation
        if (rule.jsonSchema) {
            const validate = ajv.compile(rule.jsonSchema);
            const valid = validate(record);

            if (!valid) {
                return {
                    ruleId: rule.ruleId,
                    ruleName: rule.ruleName,
                    severity: rule.severity,
                    explanation: rule.aiExplanation || 'JSON schema validation failed',
                    actualValue: record,
                };
            }
        }

        // SQL expression validation (simplified - in production, use a safe SQL executor)
        if (rule.sqlExpression) {
            const isValid = this.evaluateSqlExpression(rule.sqlExpression, record);
            if (!isValid) {
                return {
                    ruleId: rule.ruleId,
                    ruleName: rule.ruleName,
                    severity: rule.severity,
                    explanation: rule.aiExplanation || 'SQL validation failed',
                };
            }
        }

        return null;
    }

    private async executeTransformationRule(
        rule: BusinessRule,
        record: any
    ): Promise<RuleViolation | null> {
        // Transformation rules don't produce violations, they modify data
        // This would be implemented in the transformation pipeline
        return null;
    }

    private async executeConstraintRule(
        rule: BusinessRule,
        record: any
    ): Promise<RuleViolation | null> {
        // Constraint rules check business logic
        if (rule.sqlExpression) {
            const isValid = this.evaluateSqlExpression(rule.sqlExpression, record);
            if (!isValid) {
                return {
                    ruleId: rule.ruleId,
                    ruleName: rule.ruleName,
                    severity: rule.severity,
                    explanation: rule.aiExplanation || 'Constraint violation',
                };
            }
        }

        return null;
    }

    private evaluateSqlExpression(expression: string, record: any): boolean {
        // Simplified evaluation - in production, use a proper SQL evaluator
        // This is a placeholder for demonstration

        // Example: "LENGTH(gst) = 15"
        if (expression.includes('LENGTH')) {
            const match = expression.match(/LENGTH\((\w+)\)\s*=\s*(\d+)/);
            if (match) {
                const [, field, expectedLength] = match;
                const actualLength = record[field]?.length || 0;
                return actualLength === parseInt(expectedLength);
            }
        }

        // Example: "amount > 0"
        if (expression.includes('>')) {
            const match = expression.match(/(\w+)\s*>\s*(\d+)/);
            if (match) {
                const [, field, minValue] = match;
                return record[field] > parseFloat(minValue);
            }
        }

        // Example: "status IN ('ACTIVE', 'PENDING')"
        if (expression.includes('IN')) {
            const match = expression.match(/(\w+)\s+IN\s+\((.*)\)/);
            if (match) {
                const [, field, values] = match;
                const allowedValues = values.split(',').map(v => v.trim().replace(/'/g, ''));
                return allowedValues.includes(record[field]);
            }
        }

        // Default: assume valid
        logger.warn('Unable to evaluate SQL expression', { expression });
        return true;
    }

    // ============================================
    // Batch Validation
    // ============================================

    async validateBatch(
        entityName: string,
        records: any[]
    ): Promise<Map<number, RuleViolation[]>> {
        const results = new Map<number, RuleViolation[]>();

        for (let i = 0; i < records.length; i++) {
            const violations = await this.validateRecord(entityName, records[i]);
            if (violations.length > 0) {
                results.set(i, violations);
            }
        }

        return results;
    }

    // ============================================
    // Rule Statistics
    // ============================================

    async getRuleStatistics(entityName: string): Promise<{
        totalRules: number;
        activeRules: number;
        rulesByType: Record<string, number>;
        rulesBySeverity: Record<string, number;
    }> {
        const rules = await db.businessRule.findMany({
            where: { entityName },
        });

        const activeRules = rules.filter(r => r.isActive);

        const rulesByType = rules.reduce((acc, rule) => {
            acc[rule.ruleType] = (acc[rule.ruleType] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        const rulesBySeverity = rules.reduce((acc, rule) => {
            acc[rule.severity] = (acc[rule.severity] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        return {
            totalRules: rules.length,
            activeRules: activeRules.length,
            rulesByType,
            rulesBySeverity,
        };
    }
}

export const businessRulesService = new BusinessRulesService();
