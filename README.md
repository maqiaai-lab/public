# MAQIA AI

**Your ERP, but smarter.**

![Stage](https://img.shields.io/badge/stage-pre--seed-black?style=flat-square)
![Beta](https://img.shields.io/badge/beta-accepting%20testers-%23BFFF00?style=flat-square)
![Stack](https://img.shields.io/badge/stack-Next.js%20%7C%20FastAPI%20%7C%20PostgreSQL-black?style=flat-square)
![License](https://img.shields.io/badge/license-proprietary-black?style=flat-square)
![Languages](https://img.shields.io/badge/languages-EN%20%7C%20PT%20%7C%20ES%20%7C%20FR%20%7C%20DE-black?style=flat-square)

MAQIA AI is the AI-native ERP for companies that outgrew Excel or QuickBooks but can't justify SAP. Multi-company, multi-currency, built for how your business actually works — not how legacy software thinks it should. Autonomous agents handle procurement, invoicing, and reconciliation while your team stays in control through human-in-the-loop approvals.

---

## The Problem

Legacy ERPs were built for a different era. Enterprise software hasn't kept up — most ERPs were designed in the 90s and patched ever since.

- **Months-long implementations** — Traditional ERPs take 6-18 months to deploy, burning through budgets on consultants before you see any value.
- **Rigid, one-size-fits-all systems** — Legacy platforms force you to reshape your business around the software instead of the other way around.
- **Data trapped in silos** — Finance can't see procurement. Warehouse can't see demand. Every answer requires exporting CSVs and chasing people.
- **Click-heavy busywork** — Your team spends hours on manual data entry, navigating nested menus, and copying information between screens.
- **Paying for features you'll never use** — Over-engineered suites with 1,000 features — you use 10 but pay for all of them, every month.

> 70% of ERP implementations fail to meet expectations.

---

## The Difference

**AI-First, Not AI-Bolted** — Every workflow is powered by AI from the ground up. Not a chatbot stapled onto a legacy system — intelligence is woven into every action.

**Built in Minutes, Not Months** — Our AI Builder configures your entire ERP through conversation. Describe your business, and MAQIA builds the system around it. No consultants, no implementation projects.

**Pay for What You Need** — On-demand modules you enable as your business evolves. Start with procurement and finance, add inventory when you're ready. Scale up, never overpay.

**Intelligence, Not Just Data** — Anomaly detection, demand forecasting, proactive alerts. MAQIA doesn't just store your data — it understands it and tells you what to do next.

---

## How It Works

**1. Describe** — Tell MAQIA about your business — industry, workflows, entities, what matters most. Natural language, not configuration wizards.

**2. Configure** — AI builds your ERP: modules, approval chains, chart of accounts, vendor lists — tailored to your operations in minutes.

**3. Deploy** — Instant provisioning. Multi-tenant, isolated, production-ready. Import your existing data from SAP, PHC, Primavera, or CSV.

**4. Operate** — Autonomous agents handle procurement, invoicing, reconciliation. They propose actions — your team approves. Human-in-the-loop, always.

---

## By the Numbers

| | |
|---|---|
| **90%** faster ERP deployment | Minutes instead of months |
| **60%** less time on procurement | AI handles the busywork |
| **3x** faster invoice processing | OCR + AI matching |
| **0** implementation consultants | Self-service AI setup |

---

## Core Modules

### Procurement — Procure-to-Pay Automation

The complete procure-to-pay cycle managed through AI. From purchase requests to 3-way matching, all in natural language.

- **Purchase Requisitions** — Describe what you need in plain English. AI creates the PR, verifies materials against your catalog, and handles ambiguities.
- **Request for Quotation** — Generate, send, and track supplier quotes without leaving MAQIA. AI-powered vendor discovery with market research, automated email drafts, and OAuth-integrated sending via Gmail or Outlook.
- **Purchase Orders** — Convert winning quotes to POs with a single click. Zero re-entry. Or create directly from PRs.
- **Goods Receipt** — From PO line items with warehouse location assignment and serial/batch tracking.
- **Invoice Processing** — Upload PDFs or forward emails. AI reads every line item, maps it, reconciles against POs, and routes for approval.
- **3-Way Matching** — Automatic reconciliation of PO, Goods Receipt, and Invoice catches discrepancies before you pay.

### Finance & Accounting — Invoicing, GL & Intercompany

- Chart of Accounts with country-specific templates (SNC for Portugal)
- Journal entries — manual, recurring, and AI-generated
- General ledger with trial balance and account-level drill-down
- AP/AR invoicing with vendor aging reports
- SAF-T PT export for Portuguese tax authority
- Fiscal period management, tax codes, payment methods
- Financial statements: P&L, Balance Sheet
- Multi-currency with ECB exchange rates and automatic gain/loss calculation

### Inventory & Forecasting — Real-time Visibility & AI Forecasting

Know exactly what you have, where it is, and when you'll need more.

- Real-time stock levels across multiple warehouses
- Stock movement tracking and warehouse transfers
- Goods receipt with quality inspection
- AI-driven demand forecasting with trend, seasonal, and cycle detection
- Automated low-stock alerts and reorder points
- Inventory adjustments for write-offs

### Sales — Quote-to-Cash

- Quote creation with AI-powered pricing suggestions
- One-click quote to sales order conversion
- Customer management and history
- AR invoicing and revenue tracking

### Intercompany — Unified Group Operations

Run 2 to 20+ legal entities from a single workspace. Each entity gets its own chart of accounts, currency, and tax configuration — while group-level reporting gives you the full picture instantly.

- Automatic intercompany transaction matching
- AI-driven discrepancy detection and suggested corrections
- Consolidation workspace with elimination entries
- Period close checklists and IC reconciliation

### Data Migration — MigraQ

Import from SAP Business One, PHC, Primavera, or CSV. AI maps your data model automatically.

1. **Entity classification** — AI maps uploaded files to the correct target tables with confidence scoring
2. **Column mapping** — Intelligent matching using AI, learned mappings from previous migrations, and ERP-specific profiles
3. **Dependency ordering** — Automatic sequencing ensures parent records load before children
4. **Validation** — Deterministic checks (VAT, IBAN, EAN checksums) plus AI-powered anomaly detection
5. **Safe insertion** — Batched writes with full tracking and one-click rollback per migration session

---

## Capabilities

| Capability | Description |
|------------|-------------|
| **Autonomous AI Agents** | Agents that draft purchase orders, match invoices, and reconcile payments. They propose — you approve. Every action is auditable. |
| **AI Builder** | Describe your business in natural language. AI configures a fully functional ERP tailored to your industry — in minutes. |
| **Insights & Analytics** | Ask questions in plain English, build custom dashboards, receive proactive alerts about anomalies and opportunities. No SQL needed. |
| **Multi-Entity Management** | Unlimited legal entities per workspace with per-entity currency, tax config, and consolidated group reporting. |
| **Multi-Currency** | Real-time exchange rates with automatic daily updates. Period-end revaluation and unrealized gain/loss fully automated. |
| **Tax Compliance** | SNC chart of accounts, SAF-T PT generation, Spanish SII compliance — built in, not bolted on. |
| **Teams & Governance** | Role-based access control, multi-level approval chains, complete audit trails, tenant-level feature flags. |
| **Fraud Detection** | 3-way invoice matching, AI anomaly detection, multi-level approvals, vendor approval workflows, and proactive alerts. |
| **Integrations** | Gmail/Outlook email integration, invoice capture from inbox, RFQ sending via email, webhook support. |
| **5 Languages** | Full UI, AI chat, voice input, and ERP glossary in English, Portuguese, Spanish, French, and German. |

---

## Who It's For

**Multi-Entity SMEs** — Managing 2-20+ companies across borders. Manual intercompany reconciliation eating hours weekly. Need multi-currency, multi-entity without SAP complexity.

**Accounting Firms** — Managing 10-50+ client entities on different systems. Copy-pasting between PHC, Primavera, and spreadsheets. Want one platform for all clients with firm-level oversight.

**Legacy ERP Migrants** — Stuck on SAP Business One, PHC, or Primavera. Paying for features you never use and UX from 2008. Want something modern that doesn't require a 6-month project.

---

## Competitive Landscape

|  | MAQIA AI | SAP Business One | Oracle NetSuite | Odoo | Sage |
|--|----------|-----------------|-----------------|------|------|
| **Implementation cost** | Free (Beta) | $500K - $5M+ | $25K - $100K+ | $5K - $50K | $10K - $50K |
| **Time to go live** | Days | 6 - 18 months | 3 - 6 months | 1 - 3 months | 1 - 3 months |
| **Training time** | Minutes | Months | Weeks | Days | Weeks |
| **Natural language interface** | Native | No | No | No | No |
| **AI invoice OCR** | Native | Add-on | Add-on | Add-on | Add-on |
| **AI demand forecasting** | Native | No | Add-on | No | No |
| **Proactive anomaly detection** | Native | No | No | No | No |

---

## Security & Compliance

| Layer | Description |
|-------|-------------|
| **Authentication** | JWT-based with server-side validation on every request |
| **Multi-factor auth** | Optional MFA enforcement with tiered access levels |
| **Authorization** | Granular role-based access control with permission-based UI rendering |
| **Tenant isolation** | Full data isolation between tenants at the application and database layer |
| **Audit trail** | Immutable logging of every AI action. Encryption at rest and in transit. |
| **Regulatory** | SAF-T PT, SNC, SEPA XML, PSD2/Open Banking, country-specific audit configs |
| **EU AI Act** | Full transparency on AI decision-making. Human-in-the-loop by default. Auditable AI outputs across every workflow. |

---

## Tech Stack

**Frontend** — Next.js (App Router) · React · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion

**Backend** — FastAPI · LangGraph · LangChain · PostgreSQL (Row-Level Security, Realtime)

**Infrastructure** — Google Cloud Run · Docker · PostgreSQL

---

## Beta Program

We're selecting beta testers who want to shape the future of ERP. During beta, everything is free:

- All modules included
- AI Assistant with natural language queries
- Unlimited users
- Free implementation and data migration
- Priority support from the founding team
- AI-driven onboarding

**[Apply for Beta](https://maqia.ai)** — no credit card required.

---

## Contact

- **Website** — [maqia.ai](https://maqia.ai)
- **Email** — hello@maqia.ai
- **LinkedIn** — [/company/maqia](https://www.linkedin.com/company/maqia)
- **Twitter** — [@maqiaai](https://twitter.com/maqiaai)
- **GitHub** — [maqiaai-lab](https://github.com/maqiaai-lab)

---

<sub>Built in Portugal 🇵🇹</sub>
