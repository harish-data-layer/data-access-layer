require('dotenv').config();
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  // Create Vendors
  const vendor1 = await prisma.vendor.create({
    data: {
      name: "ABC Traders",
      gst: "29ABCDE1234F1Z5",
      email: "abc@vendor.com",
    },
  });

  const vendor2 = await prisma.vendor.create({
    data: {
      name: "XYZ Supplies",
      gst: "29XYZDE5678G1Z9",
      email: "xyz@vendor.com",
    },
  });

  // Create Invoices
  await prisma.invoice.createMany({
    data: [
      {
        invoiceNo: "INV-001",
        amount: 15000,
        status: "Uploaded",
        vendorId: vendor1.id,
      },
      {
        invoiceNo: "INV-002",
        amount: 22000,
        status: "Processed",
        vendorId: vendor2.id,
      },
    ],
  });

  console.log("🌱 Dummy data seeded!");
}

main()
  .catch((e) => console.error(e))
  .finally(async () => await prisma.$disconnect());
