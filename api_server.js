const express = require('express');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const port = 3001; // Using 3001 to avoid conflict with existing server on 3000

// Database connection
const pool = new Pool({
    user: process.env.POSTGRES_USER || 'postgres',
    host: 'localhost',
    database: process.env.POSTGRES_DB || 'tranai_dal',
    password: process.env.POSTGRES_PASSWORD || 'password',
    port: 5432,
});

app.use(express.json());

// Helper function for queries
const query = async (text, params) => {
    const start = Date.now();
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('Executed query', { text, duration, rows: res.rowCount });
    return res;
};

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        message: 'TranAI SAP Data API',
        endpoints: [
            '/api/summary',
            '/api/cost',
            '/api/performance',
            '/api/invoices',
            '/api/vendors',
            '/api/purchase-orders'
        ]
    });
});

// Tool Summary
app.get('/api/summary', async (req, res) => {
    try {
        const { rows } = await query('SELECT * FROM tool_summary');
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Cost Comparison
app.get('/api/cost', async (req, res) => {
    try {
        const { rows } = await query('SELECT * FROM tool_cost_comparison ORDER BY id');
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Performance Metrics
app.get('/api/performance', async (req, res) => {
    try {
        const { rows } = await query('SELECT * FROM tool_performance_metrics ORDER BY id');
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Invoices (RBKP joined with RSEG)
app.get('/api/invoices', async (req, res) => {
    try {
        const { rows } = await query(`
      SELECT 
        h.belnr, h.gjahr, h.bldat, h.lifnr, h.rmwwr, h.waers,
        i.buzei, i.matnr, i.menge, i.wrbtr
      FROM rbkp h
      JOIN rseg i ON h.belnr = i.belnr AND h.gjahr = i.gjahr
      ORDER BY h.belnr, i.buzei
    `);
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Vendors (LFA1)
app.get('/api/vendors', async (req, res) => {
    try {
        const { rows } = await query('SELECT * FROM lfa1');
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Purchase Orders (EKKO joined with EKPO)
app.get('/api/purchase-orders', async (req, res) => {
    try {
        const { rows } = await query(`
      SELECT 
        h.ebeln, h.bukrs, h.lifnr, h.bedat, h.netwr,
        i.ebelp, i.matnr, i.menge, i.netpr
      FROM ekko h
      JOIN ekpo i ON h.ebeln = i.ebeln
      ORDER BY h.ebeln, i.ebelp
    `);
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Analytics: Vendor Spend
app.get('/api/analytics/vendor-spend', async (req, res) => {
    try {
        const { rows } = await query('SELECT * FROM v_vendor_spend_analysis');
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Analytics: PO Cost Variance
app.get('/api/analytics/po-variance', async (req, res) => {
    try {
        const { rows } = await query('SELECT * FROM v_po_vs_invoice_variance');
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(port, () => {
    console.log(`API Server running at http://localhost:${port}`);
});
