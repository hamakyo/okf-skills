"""Invoice model, pricing calculation, and summary formatting."""

from __future__ import annotations

from dataclasses import dataclass

VALID_STATUSES = frozenset({"open", "paid"})


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    subtotal_cents: int
    discount_percent: int = 0
    tax_percent: int = 0
    status: str = "open"


def calculate_invoice_total(invoice: Invoice) -> int:
    """Compute final invoice total in cents (discount applied before tax)."""
    if invoice.subtotal_cents < 0:
        raise ValueError("subtotal_cents must be non-negative")
    if not 0 <= invoice.discount_percent <= 100:
        raise ValueError("discount_percent must be between 0 and 100")
    if not 0 <= invoice.tax_percent <= 100:
        raise ValueError("tax_percent must be between 0 and 100")
    if invoice.status not in VALID_STATUSES:
        raise ValueError(f"unsupported invoice status: {invoice.status!r}")

    discounted = invoice.subtotal_cents - (invoice.subtotal_cents * invoice.discount_percent // 100)
    tax = discounted * invoice.tax_percent // 100
    return discounted + tax


def format_cents(amount_cents: int) -> str:
    """Format an integer cent amount as $D.CC."""
    sign = "-" if amount_cents < 0 else ""
    whole, remainder = divmod(abs(amount_cents), 100)
    return f"{sign}${whole}.{remainder:02d}"


def format_invoice_summary(invoice: Invoice) -> str:
    """Return a compact human-readable summary for one invoice."""
    total = calculate_invoice_total(invoice)
    return f"{invoice.invoice_id} [{invoice.status}]: {format_cents(total)}"
