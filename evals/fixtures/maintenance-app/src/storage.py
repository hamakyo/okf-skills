"""Minimal in-memory invoice repository."""

from __future__ import annotations

from src.invoices import Invoice


class InMemoryInvoiceStore:
    def __init__(self) -> None:
        self._items: dict[str, Invoice] = {}

    def add_invoice(self, invoice: Invoice) -> None:
        self._items[invoice.invoice_id] = invoice

    def get_invoice(self, invoice_id: str) -> Invoice | None:
        return self._items.get(invoice_id)

    def list_invoices(self) -> list[Invoice]:
        return list(self._items.values())
