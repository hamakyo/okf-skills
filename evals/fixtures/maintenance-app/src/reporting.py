"""Read-only invoice aggregation and monthly report formatting."""

from __future__ import annotations

from collections.abc import Iterable

from src.invoices import VALID_STATUSES, Invoice, calculate_invoice_total, format_cents


def summarize_invoices(invoices: Iterable[Invoice]) -> dict[str, int]:
    """Aggregate invoice counts and cent totals by status."""
    count = 0
    open_cents = 0
    paid_cents = 0
    for invoice in invoices:
        if invoice.status not in VALID_STATUSES:
            raise ValueError(f"unsupported invoice status: {invoice.status!r}")
        total = calculate_invoice_total(invoice)
        count += 1
        if invoice.status == "open":
            open_cents += total
        else:
            paid_cents += total
    return {
        "count": count,
        "open_cents": open_cents,
        "paid_cents": paid_cents,
        "total_cents": open_cents + paid_cents,
    }


def format_monthly_report(invoices: Iterable[Invoice]) -> str:
    """Render a multi-line monthly invoice summary report."""
    count = 0
    open_cents = 0
    paid_cents = 0
    for invoice in invoices:
        if invoice.status not in VALID_STATUSES:
            raise ValueError(f"unsupported invoice status: {invoice.status!r}")
        total = calculate_invoice_total(invoice)
        count += 1
        if invoice.status == "open":
            open_cents += total
        else:
            paid_cents += total
    total_cents = open_cents + paid_cents
    return "\n".join(
        [
            f"Invoices: {count}",
            f"Open: {format_cents(open_cents)}",
            f"Paid: {format_cents(paid_cents)}",
            f"Total: {format_cents(total_cents)}",
        ]
    )
