import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

async function main() {
    console.log('🌱 Seeding database...');

    // 1. Create Semantic Entities
    const vendorEntity = await prisma.entity.upsert({
        where: { entityId: 'ENT-VENDOR-001' },
        update: {},
        create: {
            entityId: 'ENT-VENDOR-001',
            entityName: 'Vendor',
            businessDefinition: 'Supplier master data for procurement',
            businessOwner: 'Procurement Department',
            dataSteward: 'John Doe',
            sourceSystem: 'SAP ECC',
            domain: 'Procurement',
            dataClassification: 'Internal',
            complianceTags: ['GDPR'],
            retentionPolicy: '7 Years',
            versionId: 'v1.0.0',
            effectiveFrom: new Date(),
        },
    });

    const invoiceEntity = await prisma.entity.upsert({
        where: { entityId: 'ENT-INVOICE-001' },
        update: {},
        create: {
            entityId: 'ENT-INVOICE-001',
            entityName: 'Invoice',
            businessDefinition: 'Financial document for payments',
            businessOwner: 'Finance Department',
            dataSteward: 'Jane Smith',
            sourceSystem: 'SAP ECC',
            domain: 'Finance',
            dataClassification: 'Confidential',
            complianceTags: ['Tax-Reg'],
            retentionPolicy: '10 Years',
            versionId: 'v1.0.0',
            effectiveFrom: new Date(),
        },
    });

    // 2. Create Attributes
    await prisma.attribute.upsert({
        where: { attributeId: 'ATTR-VEND-NAME' },
        update: {},
        create: {
            attributeId: 'ATTR-VEND-NAME',
            entityId: vendorEntity.entityId,
            attributeName: 'vendorName',
            dataType: 'String',
            businessDefinition: 'Legal name of the vendor',
            isSensitive: false,
        },
    });

    await prisma.attribute.upsert({
        where: { attributeId: 'ATTR-INV-NUM' },
        update: {},
        create: {
            attributeId: 'ATTR-INV-NUM',
            entityId: invoiceEntity.entityId,
            attributeName: 'invoiceNumber',
            dataType: 'String',
            businessDefinition: 'Unique invoice identifier',
            isSensitive: false,
        },
    });

    // 3. Create Curated Vendors
    await prisma.curatedVendor.createMany({
        data: [
            {
                vendorId: 'VEND-001',
                vendorCode: 'ABC-123',
                vendorName: 'ABC Global Trading',
                gst: '29ABCDE1234F1Z5',
                validFrom: new Date(),
                isCurrent: true,
                dqScore: 0.98,
            },
            {
                vendorId: 'VEND-002',
                vendorCode: 'XYZ-456',
                vendorName: 'XYZ Industrial Supplies',
                gst: '29XYZDE5678G1Z9',
                validFrom: new Date(),
                isCurrent: true,
                dqScore: 0.95,
            }
        ],
        skipDuplicates: true,
    });

    // 4. Create Curated Invoices
    await prisma.curatedInvoice.createMany({
        data: [
            {
                invoiceId: 'INV-1001',
                invoiceNumber: '7890123',
                vendorId: 'VEND-001',
                invoiceDate: new Date(),
                totalAmount: 45000.00,
                status: 'PAID',
                validFrom: new Date(),
                isCurrent: true,
                dqScore: 0.99,
            },
            {
                invoiceId: 'INV-1002',
                invoiceNumber: '7890124',
                vendorId: 'VEND-002',
                invoiceDate: new Date(),
                totalAmount: 12500.50,
                status: 'PENDING',
                validFrom: new Date(),
                isCurrent: true,
                dqScore: 0.92,
            }
        ],
        skipDuplicates: true,
    });

    console.log('✅ Seeding completed successfully!');
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });
