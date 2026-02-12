require("dotenv").config();
const { PrismaClient } = require("@prisma/client");
const xlsx = require("xlsx");

const prisma = new PrismaClient();

// Load Excel
const workbook = xlsx.readFile("huge_synthetic_sap_data_v3.xlsx");

// Read sheets
const vendorsData = xlsx.utils.sheet_to_json(workbook.Sheets["Vendors"]);
const poData = xlsx.utils.sheet_to_json(workbook.Sheets["Purchase_Orders"]);
const invoiceData = xlsx.utils.sheet_to_json(workbook.Sheets["Invoices"]);

async function importAll() {
  console.log("🚀 Starting import...");

  // =============================
  // STEP 1 — Import Vendors
  // =============================

  const vendorMap = {};

  for (const row of vendorsData) {
    const vendor = await prisma.vendor.create({
      data: {
        vendorCode: row.vendor_id?.toString(),
        name: row.vendor_name,
        gst: row.gst_number,
        email: row.email,
        phone: row.phone,
        address: row.address,
        city: row.city,
        state: row.state,
        country: row.country,
        postalCode: row.postal_code,
        bankName: row.bank_name,
        bankAccount: row.bank_account,
        ifscCode: row.ifsc_code,
        paymentTerms: row.payment_terms,
        currency: row.currency,
        status: row.status,
        contactPerson: row.contact_person,
        contactPhone: row.contact_phone,
        notes: row.notes
      }
    });

    vendorMap[row.vendor_id] = vendor.id;
  }

  console.log("✅ Vendors imported");

  // =============================
  // STEP 2 — Import Purchase Orders
  // =============================

  console.log("📦 Importing Purchase Orders...");

  for (const row of poData) {
    const vendorId = vendorMap[row.vendor_id];
    if (!vendorId) continue;

    await prisma.purchaseOrder.create({
      data: {
        poNumber: String(row.po_id),

        vendorId: vendorId,
        amount: Number(row.amount || 0),
        currency: row.currency || "INR",
        status: row.po_status || "CREATED",
        paymentTerms: row.payment_terms || "Net30",
        department: row.department || "General",

        taxAmount: Number(row.tax || 0),
        totalAmount: Number(row.amount || 0) - Number(row.discount || 0),

        notes: row.remarks || ""
      }
    });
  }

  console.log("✅ Purchase Orders imported");

  // =============================
  // STEP 3 — Import Invoices
  // =============================

  console.log("🧾 Importing Invoices...");

  for (const row of invoiceData) {
    const vendorId = vendorMap[row.vendor_id];
    if (!vendorId) continue;

    await prisma.invoice.create({
      data: {
        invoiceNo: String(row.invoice_id),

        vendorId: vendorId,
        poNumber: String(row.po_number || ""),
        amount: Number(row.amount || 0),
        taxAmount: Number(row.tax_amount || 0),
        totalAmount: Number(row.total_amount || 0),

        currency: row.currency || "INR",
        status: row.status || "PENDING",
        paymentMethod: row.payment_method || "BANK",

        notes: row.notes || ""
      }
    });
  }

  console.log("✅ Invoices imported");
  console.log("🎉 ALL DATA IMPORTED SUCCESSFULLY");
}

importAll()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
