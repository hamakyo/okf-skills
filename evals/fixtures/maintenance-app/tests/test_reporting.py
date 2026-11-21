import unittest

from src.invoices import Invoice
from src.reporting import format_monthly_report, summarize_invoices


class ReportingTests(unittest.TestCase):
    def test_summarize_and_format_mixed_invoices(self) -> None:
        invoices = [
            Invoice(invoice_id="INV-1", subtotal_cents=1000, status="open"),
            Invoice(invoice_id="INV-2", subtotal_cents=2500, status="paid"),
        ]
        summary = summarize_invoices(invoices)
        self.assertEqual(
            summary,
            {"count": 2, "open_cents": 1000, "paid_cents": 2500, "total_cents": 3500},
        )
        report = format_monthly_report(invoices)
        self.assertEqual(
            report,
            "Invoices: 2\nOpen: $10.00\nPaid: $25.00\nTotal: $35.00",
        )


if __name__ == "__main__":
    unittest.main()
