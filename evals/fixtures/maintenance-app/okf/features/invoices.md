---
type: Feature
title: Invoices
description: Pricing rules, statuses, and summary formatting for customer invoices.
tags: [feature, invoices]
---

# Pricing Rules

- `subtotal_cents` must be a non-negative integer.
- `discount_percent` must be an integer from `0` through `100` inclusive.
- `tax_percent` must be an integer from `0` through `100` inclusive.
- Percentage discounts apply to `subtotal_cents` **before** tax:
  - `discounted = subtotal_cents - (subtotal_cents * discount_percent // 100)`
  - `tax = discounted * tax_percent // 100`
  - `total = discounted + tax`

# Statuses And Formatting

- Supported statuses are `"open"` and `"paid"`.
- `format_invoice_summary(invoice)` formats an invoice as `<invoice_id> [<status>]: $<dollars>.<cents>`.
