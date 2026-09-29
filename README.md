# 🌿 GreenVision — Odoo 18 Enterprise Suite

[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-714B67?style=for-the-badge&logo=odoo&logoColor=white)](https://www.odoo.com)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/lgpl-3.0.html)
[![Integration](https://img.shields.io/badge/Integrations-Tally%20Prime%20%7C%20Shopify-brightgreen?style=for-the-badge)](https://www.greenvision.in)

> **Enterprise Resource Planning (ERP) ecosystem for GreenVision ([greenvision.in](https://www.greenvision.in)) built on Odoo 18.**  
> Unifying core operations, advanced e-commerce synchronization, accounting integration with Tally ERP, and employee performance tracking into a modular architecture.

---

## 📑 Table of Contents

- [System Architecture](#-system-architecture)
- [Modules Overview](#-modules-overview)
  - [1. GreenVision Core (`green_vision`)](#1-greenvision-core-green_vision)
  - [2. Tally Integration Framework (`odoo18_tally_sync`)](#2-tally-integration-framework-odoo18_tally_sync)
  - [3. Shopify E-Commerce Sync (`odoo18_shopify_sync`)](#3-shopify-e-commerce-sync-odoo18_shopify_sync)
  - [4. Employee Performance Management (`employee_performance_management`)](#4-employee-performance-management-employee_performance_management)
- [Repository Structure](#-repository-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Module Configuration](#-module-configuration)
  - [Tally Sync Setup](#tally-sync-setup)
  - [Shopify Sync Setup](#shopify-sync-setup)
  - [HR Performance Setup](#hr-performance-setup)
- [Sync Workflows & Services](#-sync-workflows--services)
- [Security & Access Rights](#-security--access-rights)
- [License](#-license)

---

## 🏛 System Architecture

```text
                       ┌───────────────────────────────┐
                       │       Shopify Store           │
                       │   (Orders, Products, Cust.)   │
                       └───────────────┬───────────────┘
                                       │ REST / Admin API
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                        Odoo 18 ERP (GreenVision)                          │
 │                                                                           │
 │   ┌───────────────────────┐          ┌────────────────────────────────┐   │
 │   │     green_vision      │          │ employee_performance_mgmt     │   │
 │   │  • Executive Dashboard│          │  • KRA / KPA / KPI Framework   │   │
 │   │  • Strict Picking Val.│          │  • DSR (Daily Status Report)   │   │
 │   │  • MRP & Role Views   │          │  • Evaluation & Scorecards     │   │
 │   └───────────┬───────────┘          └────────────────┬───────────────┘   │
 │               │                                       │                   │
 │               └───────────────────┬───────────────────┘                   │
 │                                   │                                       │
 │                       ┌───────────▼───────────┐                           │
 │                       │   odoo18_tally_sync   │                           │
 │                       │  • XML HTTP Engine    │                           │
 │                       │  • Ledger/Voucher Sync│                           │
 │                       └───────────┬───────────┘                           │
 └───────────────────────────────────┼───────────────────────────────────────┘
                                     │ XML over HTTP (Port 9000)
                                     ▼
                       ┌───────────────────────────────┐
                       │       Tally Prime / ERP 9     │
                       │ (Vouchers, Ledgers, Tax, GST) │
                       └───────────────────────────────┘
```

---

## 📦 Modules Overview

### 1. GreenVision Core (`green_vision`)
Central customizations tailoring standard Odoo workflows to GreenVision's operational standards:
- **Interactive Executive Dashboard**: Custom OWL widget delivering immediate visibility into total sales revenue, pending purchase approvals, outstanding receivables/payables, manufacturing output, and inventory counts.
- **Strict Stock Picking Validation**: Intercepts delivery orders to ensure stock availability before confirmation, preventing negative stock levels and fulfillment discrepancies.
- **Role-Based Product Masking**: Implements `group_show_product_reference` security rules to conditionally reveal or conceal internal codes and technical SKUs depending on user roles.

### 2. Tally Integration Framework (`odoo18_tally_sync`)
A robust, bi-directional integration connector syncing Odoo 18 with Tally Prime / ERP 9 using direct XML over HTTP:
- **Master Data Synchronization**:
  - **Customers**: Synced directly to Tally *Sundry Debtors* with GSTIN, state, address, and credit limits.
  - **Vendors**: Synced to Tally *Sundry Creditors*.
  - **Products**: Synced to Tally *Stock Items* with units of measure, HSN codes, and pricing.
- **Voucher & Accounting Synchronization**:
  - **Customer Invoices** $\rightarrow$ Tally *Sales Vouchers*.
  - **Vendor Bills** $\rightarrow$ Tally *Purchase Vouchers*.
  - **Payments & Receipts** $\rightarrow$ Tally *Payment* and *Receipt Vouchers*.
  - **Credit Notes** $\rightarrow$ Tally *Credit Notes* (Sales Returns).
  - **Debit Notes** $\rightarrow$ Tally *Debit Notes* (Purchase Returns).
- **Execution & Observability**:
  - **Detailed Audit Trail**: Every XML request and response is stored in `tally.sync.log` with status indicators.
  - **Manual & Automated Modes**: Run interactive sync via manual wizards, bulk server actions from tree views, or scheduled background cron jobs.

### 3. Shopify E-Commerce Sync (`odoo18_shopify_sync`)
Automates data flow between online storefronts and backend operations:
- **Order Pipeline**: Ingests orders, aligns customer profiles, creates matching `sale.order` records, and initializes picking/invoicing.
- **Product & Inventory Realignment**: Synchronizes catalog items and tracks inventory across channels.
- **Financial Mapping**: Maps payment methods and gateway transactions to Odoo accounting journals.
- **Sync History**: Tracks batch runs and error reporting through dedicated sync logs.

### 4. Employee Performance Management (`employee_performance_management`)
A structured, metrics-driven HR evaluation and appraisal framework:
- **Performance Hierarchy**:
  - **KRA** (Key Result Areas) $\rightarrow$ **KPA** (Key Performance Areas) $\rightarrow$ **KPI** (Key Performance Indicators).
  - Configurable weightages, target benchmarks, and rating scales (1–5 scale).
- **Templates & Job Alignment**:
  - Pre-configure appraisal templates mapped to Job Positions (`hr.job`), with the ability to define employee-specific overrides.
- **Task Management**:
  - Distinguishes between fixed operational responsibilities and dynamic project tasks (`project.task`).
- **Daily Status Reports (DSR)**:
  - Daily submission workflow for team members detailing hours and task progress.
  - Manager review, feedback loop, and approval mechanism.
- **Review Cycles & Evaluations**:
  - Supports Monthly, Quarterly, and Annual review cycles with self-assessment, manager reviews, and computed scorecards.

---

## 📂 Repository Structure

```text
.
├── employee_performance_management/      # HR appraisal, KPI/KRA, and DSR suite
│   ├── data/                             # Sequences, rating scales, and master data
│   ├── models/                           # KRA, KPA, KPI, DSR, assignment, and evaluations
│   ├── security/                         # Access rules and user/manager security groups
│   └── views/                            # Performance dashboards, review cycles, and DSR views
├── green_vision/                         # Core customizations, dashboards, and stock validations
│   ├── models/                           # Dashboard statistics, stock pickings, and products
│   ├── security/                         # Custom permissions (e.g., product code masking)
│   ├── static/src/                       # OWL dashboard components (JS, XML, CSS)
│   └── views/                            # Extended views for pickings, products, and dashboard
├── odoo18_shopify_sync/                  # Shopify API connector and order processing
│   ├── data/                             # Scheduled cron jobs for sync polling
│   ├── models/                           # Instances, sync logs, partner/order mappings
│   ├── security/                         # User permissions and ACL
│   └── views/                            # Shopify instances, orders, and log monitors
└── odoo18_tally_sync/                    # Tally Prime XML-over-HTTP integration framework
    ├── data/                             # Automated sync cron jobs
    ├── models/                           # Configurations, journal mappings, and sync logs
    ├── security/                         # Module permissions and ACL
    ├── services/                         # XML generator, parser, and HTTP client services
    ├── views/                            # Vouchers, partner sync tabs, configuration, and logs
    └── wizard/                           # Manual batch synchronization wizard
```

---

## ⚡ Prerequisites

| Requirement | Supported Version | Notes |
| :--- | :--- | :--- |
| **Odoo** | `18.0` (Community or Enterprise) | Target platform |
| **Python** | `3.10` / `3.12` | Runtime environment |
| **PostgreSQL** | `14.0+` | Database engine |
| **Tally** | Tally Prime / Tally ERP 9 | ODBC / XML Server enabled (default port `9000`) |
| **Shopify** | Shopify Admin API (2024-xx) | Custom App with Read/Write API Access Tokens |

---

## 🚀 Installation & Setup

1. **Clone the Repository** into your custom addons directory:
   ```bash
   cd /path/to/odoo/custom_addons
   git clone https://github.com/ashurohom/Green-Vision-DW.git greenvision
   ```

2. **Update Odoo Configuration (`odoo.conf`)**:
   Add the path to the `addons_path` directive:
   ```ini
   addons_path = /path/to/odoo/addons,/path/to/odoo/custom_addons/greenvision
   ```

3. **Install Dependencies**:
   Ensure required Python packages are available in your Odoo virtual environment:
   ```bash
   pip install requests urllib3
   ```

4. **Update App List & Install**:
   - Restart the Odoo server.
   - Activate **Developer Mode** in the Odoo web interface.
   - Navigate to **Apps** $\rightarrow$ click **Update Apps List**.
   - Search for each module and click **Install**:
     - `green_vision`
     - `odoo18_tally_sync`
     - `odoo18_shopify_sync`
     - `employee_performance_management`

---

## ⚙️ Module Configuration

### Tally Sync Setup
1. Go to **Tally Integration** $\rightarrow$ **Configuration**.
2. Provide:
   - **Tally Server Host / IP**: e.g., `127.0.0.1` or server local IP.
   - **Tally Server Port**: default is `9000`.
   - **Company Name**: Exact name matching your company in Tally Prime.
   - **Default Accounts**: Configure sales/purchase/discount ledger fallbacks.
3. Test connection using **Test Connection** before running sync.
4. Set automated schedules in **Scheduled Actions** or use **Manual Sync Wizard** for bulk backfills.

### Shopify Sync Setup
1. Navigate to **Shopify Sync** $\rightarrow$ **Instances**.
2. Enter your Shopify Store URL (`https://your-store.myshopify.com`) and **Admin API Access Token**.
3. Choose financial journals and warehouse routing for imported orders.
4. Enable the automated cron or trigger imports manually via the instance action buttons.

### HR Performance Setup
1. Go to **Performance Management** $\rightarrow$ **Configuration**.
2. Define standard **Rating Scales** (e.g., 1–5 performance metrics).
3. Set up **KRAs, KPAs, and KPIs** with target thresholds and relative weights.
4. Assemble **Performance Templates** and attach them to target **Job Positions**.
5. Assign templates to employees and begin daily or monthly **DSR** and **Evaluation** cycles.

---

## 🔄 Sync Workflows & Services

The integration modules isolate business logic in dedicated service classes:

- **`TallyClient`** (`services/tally_client.py`): Handles HTTP communication, network timeouts, and raw payload transmission to Tally.
- **`XmlGenerator`** (`services/xml_generator.py`): Builds clean XML envelopes conforming to Tally's schema for Master entries and multi-line Accounting Vouchers.
- **`XmlParser`** (`services/xml_parser.py`): Decodes Tally's response envelopes, handling error codes, duplicate alerts, and ledger status values.

---

## 🔒 Security & Access Rights

- **GreenVision Product Reference Security**: Restricted group (`green_vision.group_show_product_reference`) for viewing internal SKUs and references.
- **Tally Integration**: Separate User and Manager access groups governing configuration edits vs. operational viewing.
- **Performance Management**: Segregated permissions for Employees (submit DSR, view assigned KPIs), Managers (evaluate, review DSR), and HR Administrators (full cycle management).

---

## 📄 License

This repository and its custom modules are licensed under the [GNU Lesser General Public License v3.0 (LGPL-3)](https://www.gnu.org/licenses/lgpl-3.0.html).

---

<p align="center">
  <b>Developed for GreenVision</b> • <a href="https://www.greenvision.in">www.greenvision.in</a>
</p>
