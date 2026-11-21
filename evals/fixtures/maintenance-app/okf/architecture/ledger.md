---
type: Architecture
title: Ledger Architecture
description: Defines module boundaries between invoice pricing, reporting, and in-memory storage.
tags: [architecture, ledger]
---

# Module Boundaries

| Module | Responsibility |
| --- | --- |
| `src/invoices.py` | Invoice data model, discount/tax calculation, and single-invoice summary formatting. |
| `src/reporting.py` | Read-only invoice aggregation and monthly text report generation. |
| `src/storage.py` | In-memory invoice store supporting add, get, and list operations. |

# Storage Invariants

- `InMemoryInvoiceStore` stores invoices keyed by `invoice_id` in insertion order.
- `add_invoice` currently overwrites an existing entry with the same `invoice_id`.
