const express = require('express');
const { PrismaClient } = require('@prisma/client');

const app = express();
const prisma = new PrismaClient();

app.use(express.json());

// Create Vendor
app.post('/vendor', async (req, res) => {
  const vendor = await prisma.vendor.create({
    data: req.body,
  });
  res.json(vendor);
});

// Get Vendors
app.get('/vendors', async (req, res) => {
  const vendors = await prisma.vendor.findMany();
  res.json(vendors);
});

// Create Invoice
app.post('/invoice', async (req, res) => {
  const invoice = await prisma.invoice.create({
    data: req.body,
  });
  res.json(invoice);
});

// Get Invoices
app.get('/invoices', async (req, res) => {
  const invoices = await prisma.invoice.findMany({
    include: { vendor: true },
  });
  res.json(invoices);
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
