
🚀 TranAI Data Access Layer (DAL)

This repository contains the Data Access Layer (DAL) implementation for the TranAI platform. The DAL acts as an intermediary layer between external enterprise systems (such as SAP) and the application services, ensuring secure, structured, and scalable data management.

📌 Project Overview

The primary objective of this module is to design and implement a synthetic SAP-like data pipeline that:

Simulates SAP enterprise data structures

Imports large-scale structured data into a PostgreSQL database

Uses Prisma ORM for schema management and database operations

Enables scalable ETL workflows for future integrations

This serves as the foundational data layer for AI agents such as:

Vendor Invoice Management Agent (VIM)

Financial Copilot Agent

GenBI Analytics Agent

🏗️ System Architecture
Synthetic SAP Data Source (Excel / API)
            ↓
   ETL Import Pipeline (Node.js + Prisma)
            ↓
     PostgreSQL Database (DAL)
            ↓
       Application Services / AI Agents

🧰 Tech Stack
Component	Technology
Database	PostgreSQL
ORM	Prisma
Backend Runtime	Node.js
Data Processing	XLSX Parser
Version Control	Git + GitHub
Development Environment	Cursor IDE
📊 Synthetic SAP Data Simulation

Since a live SAP connection was not available during development, a synthetic SAP dataset was generated to simulate real enterprise conditions.

The dataset includes:

Vendor Master Data

Vendor identification details

GST information

Contact and banking details

Purchase Orders

PO numbers

Vendor relationships

Financial transaction details

Invoice Records

Invoice references

Payment status

Tax and total amounts

Each dataset contains ~1000+ records to replicate enterprise-scale workloads.

⚙️ Database Schema Design

The DAL schema was designed using Prisma ORM and includes three primary relational entities:

1️⃣ Vendor

Stores supplier master information.

2️⃣ PurchaseOrder

Stores procurement transaction data linked to vendors.

3️⃣ Invoice

Stores financial invoice records linked to vendors and purchase orders.

Relational integrity is maintained using foreign keys.

🔄 ETL Data Import Pipeline

A custom ETL script was developed to:

Extract data from Excel sheets

Transform data into normalized JSON format

Load records into PostgreSQL using Prisma ORM

Maintain relational mappings between tables

Key features of the pipeline:

Automatic vendor ID mapping

Bulk data insertion support

Error handling for missing values

Configurable data transformation logic

🧪 How to Run the Import Pipeline
1️⃣ Install Dependencies
npm install

2️⃣ Configure Database Connection

Update the .env file:

DATABASE_URL="postgresql://username:password@localhost:5433/tranai_db"

3️⃣ Run Prisma Migration
npx prisma migrate dev

4️⃣ Execute Data Import Script
node importAll.js


This will populate all tables with synthetic SAP data.

📈 Current Capabilities

✔ Prisma-based relational schema
✔ Large-scale synthetic data ingestion
✔ ETL pipeline automation
✔ SAP-like enterprise data modeling
✔ Git-based collaborative workflow

🔮 Future Enhancements

Planned product-level improvements include:

Real-time SAP database connectors

Incremental data synchronization

Data validation and reconciliation engine

API layer for data access

Automated ETL scheduling

Cloud deployment readiness