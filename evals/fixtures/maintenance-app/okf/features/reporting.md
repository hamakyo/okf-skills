---
type: Feature
title: Reporting
description: Aggregates invoice totals by status and renders compact monthly summaries.
tags: [feature, reporting]
---

# Behavior

- `summarize_invoices(invoices)` returns `{"count", "open_cents", "paid_cents", "total_cents"}`.
- Raises `ValueError` if an invoice has an unsupported status.
- `format_monthly_report(invoices)` renders a multi-line summary showing count, open total, paid total, and grand total.
- Tie-breaking order for unrelated custom sorts is intentionally unspecified.
