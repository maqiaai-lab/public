# MAQIA AI

**Intelligent ERP for the companies in between.**

![Stage](https://img.shields.io/badge/stage-pre--seed-black?style=flat-square)
![Stack](https://img.shields.io/badge/stack-Next.js%20%7C%20FastAPI%20%7C%20Supabase-black?style=flat-square)
![License](https://img.shields.io/badge/license-proprietary-black?style=flat-square)
![Languages](https://img.shields.io/badge/languages-EN%20%7C%20PT%20%7C%20ES%20%7C%20FR%20%7C%20DE-black?style=flat-square)

MAQIA AI is a multi-tenant ERP platform built for companies that outgrew Excel but can't justify SAP. We combine AI-driven workflow orchestration with deep European regulatory compliance to deliver accounting, procurement, inventory, and financial operations through a conversational interface — without the legacy baggage. Purpose-built for SMEs and mid-market companies that need real infrastructure, not watered-down enterprise software.

---

## Why MAQIA AI

- **AI-native from day one** — Not a chatbot bolted onto a spreadsheet. AI agents orchestrate multi-step workflows: automated journal entries, end-to-end procurement, and intelligent data migration with semantic validation. Every operation flows through a human-in-the-loop approval layer before committing.

- **Multi-tenant, multi-company, multi-currency** — Built for European complexity. Manage multiple legal entities, currencies, and consolidation hierarchies from a single platform. Intercompany transactions, elimination entries, and group-level reporting are first-class features.

- **Full regulatory compliance** — SAF-T PT export, SNC chart of accounts, SEPA XML payments, PSD2/Open Banking readiness. Country-specific audit configurations. Compliance isn't an add-on — it's the foundation.

- **Modern stack, no legacy wrappers** — Next.js, FastAPI, LangGraph, Supabase. Every component was chosen for what's possible today, not constrained by decisions made in 2004.

- **Designed for the middle market** — Purpose-built for companies with real operational complexity but without enterprise budgets. Configurable per tenant, granular role-based access, and multi-language support across five languages.

---

## Platform Overview

MAQIA AI is structured as a conversational ERP where AI agents handle operational workflows end-to-end:

```
User request
  → Intelligent routing (intent classification + domain detection)
    → Domain agent (Finance / Procurement / Inventory / Sales)
      → Task execution (extraction, validation, enrichment)
        → Human approval gate
          → Database commit
```

**Conversational interface** — Users interact through natural language. The system classifies intent, routes to the appropriate domain, and executes multi-step operations with real-time streaming responses.

**Hybrid intelligence** — Fast-path rules handle routine interactions instantly. AI classification engages only when needed, keeping response times low without sacrificing accuracy.

**Persistent context** — Conversations maintain state across sessions. The system tracks domain context, detects language switches, and avoids re-asking for information already provided.

**Multi-language** — All interactions support English, Portuguese, Spanish, French, and German. Language is auto-detected per message and persisted across sessions.

---

## Core Modules

### Finance & Accounting

- Chart of Accounts with country-specific templates (SNC for Portugal)
- Journal entries — manual, recurring, and AI-generated
- General ledger with trial balance and account-level drill-down
- AP/AR invoicing with vendor aging reports
- SAF-T PT export for Portuguese tax authority
- Fiscal period management, tax codes, payment methods
- Financial statements: P&L, Balance Sheet
- Multi-currency with ECB exchange rates and automatic gain/loss calculation

### Procurement

Full procure-to-pay cycle with AI-assisted automation:

- **Purchase Requisitions** — Conversational creation with intelligent material extraction, real-time product catalog verification, and candidate disambiguation when matches are ambiguous.
- **Request for Quotation** — Multi-PR support, AI-powered vendor discovery with market research, automated email drafts, and OAuth-integrated sending via Gmail or Outlook.
- **Purchase Orders** — Created from RFQs, PRs, or directly. Line item validation against product catalog.
- **Goods Receipt** — From PO line items with warehouse location assignment and serial/batch tracking.
- **Invoice Processing** — Email ingestion from Gmail and Outlook, OCR extraction from invoice PDFs, automatic PO line reconciliation, and approval routing.

Covers the full lifecycle: creation, editing, copying, deletion, plus goods receipt, service entry, return orders, and supplier evaluation.

### Inventory & Forecasting

- Stock levels by warehouse and product with low-stock alerts
- Stock movement tracking and warehouse transfers
- Goods receipt from purchase orders
- Demand forecasting with trend, seasonal, and cycle detection
- Automated replenishment recommendations
- Scheduled forecast updates

### Intercompany

- Transaction tracking across legal entities
- Relationship rules: Standard, Netting, Recharge, Loan
- Consolidation workspace with automatic elimination entries
- Period close checklists
- Intercompany reconciliation
- AI-powered recommendations for intercompany packages

### Sales

- Sales order management
- AR invoicing and tracking

### Data Migration — MigraQ

AI-powered pipeline for migrating from legacy ERPs (SAP, Odoo, QuickBooks, Primavera):

1. **Entity classification** — AI maps uploaded files to the correct target tables with confidence scoring
2. **Column mapping** — Intelligent matching using AI, learned mappings from previous migrations, and ERP-specific profiles
3. **Dependency ordering** — Automatic sequencing ensures parent records load before children
4. **Data transformation** — Date normalization, currency handling, boolean conversion, status code mapping
5. **Validation** — Deterministic checks (VAT, IBAN, EAN checksums, type/format) plus AI-powered anomaly detection
6. **Safe insertion** — Batched writes with full tracking and one-click rollback per migration session

---

## Approvals & Workflows

Every write operation flows through a configurable approval layer:

- **Supported entities:** Purchase Requisitions, RFQs, Purchase Orders, Invoices, Products, Intercompany Transactions, Vendor Records
- **Role-based routing** with granular, configurable permissions
- **Visual workflow builder** for custom approval chains
- **Full audit trail** — requester info, line items, amounts, and approval metadata
- **Real-time notifications** — instant push when approvals are pending or resolved

---

## Security & Compliance

| Layer | Description |
|-------|-------------|
| **Authentication** | JWT-based with server-side validation on every request |
| **Multi-factor auth** | Optional MFA enforcement with tiered access levels |
| **Authorization** | Granular role-based access control with permission-based UI rendering |
| **Tenant isolation** | Full data isolation between tenants at the application and database layer |
| **Session security** | Auto-logout on idle, secure session management |
| **Regulatory** | SAF-T PT, SNC chart of accounts, SEPA XML, PSD2/Open Banking, country-specific audit configs |

---

## Integrations

| Integration | Purpose |
|-------------|---------|
| **Gmail / Google Workspace** | Invoice email ingestion, RFQ sending via OAuth |
| **Microsoft 365 / Outlook** | Invoice email ingestion, RFQ sending via OAuth |
| **OCR / Document AI** | Automatic extraction from invoice PDFs |
| **ECB Exchange Rates** | Multi-currency rate updates |
| **Natural language queries** | Ask questions about your data in plain language |

---

## Tech Stack

**Frontend**
- Next.js (App Router) · React · TypeScript
- Tailwind CSS · shadcn/ui · Framer Motion
- Tremor · Recharts · Plotly (financial visualizations)
- Phosphor Icons · PP Neue Montreal typeface

**Backend**
- FastAPI (async, streaming)
- LangGraph · LangChain
- Supabase (Postgres, Row-Level Security, Realtime)

**Infrastructure**
- Google Cloud Run
- Docker
- Supabase (auth, storage, database, realtime)

---

## Localization

MAQIA AI supports five languages across the full stack:

| Language | UI | AI Chat | Voice Input | ERP Glossary |
|----------|:--:|:-------:|:-----------:|:------------:|
| English | x | x | x | x |
| Portuguese (PT) | x | x | x | x |
| Spanish | x | x | x | x |
| French | x | x | x | x |
| German | x | x | x | x |

Language is auto-detected per message in chat, persisted across sessions, and configurable as a tenant-level default.

---

## Status

MAQIA AI is in **pre-seed stage**, actively building core modules. We're onboarding early design partners — accounting firms and mid-market companies in Portugal and across Europe.

Interested in early access? Reach out below.

---

## Contact

- **Website** — [maqia.ai](https://maqia.ai)
- **LinkedIn** — [MAQIA AI](https://www.linkedin.com/company/maqia)
- **Email** — hello@maqia.ai

---

<sub>Built in Portugal 🇵🇹</sub>
