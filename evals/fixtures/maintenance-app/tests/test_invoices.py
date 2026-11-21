import unittest

from src.invoices import Invoice, calculate_invoice_total, format_invoice_summary


class InvoiceTests(unittest.TestCase):
    def test_total_without_discount_or_tax(self) -> None:
        inv = Invoice(invoice_id="INV-100", subtotal_cents=2500)
        self.assertEqual(calculate_invoice_total(inv), 2500)

    def test_total_with_discount_only(self) -> None:
        inv = Invoice(invoice_id="INV-101", subtotal_cents=2000, discount_percent=25)
        self.assertEqual(calculate_invoice_total(inv), 1500)

    def test_total_with_tax_only(self) -> None:
        inv = Invoice(invoice_id="INV-102", subtotal_cents=2000, tax_percent=10)
        self.assertEqual(calculate_invoice_total(inv), 2200)

    def test_format_invoice_summary(self) -> None:
        inv = Invoice(invoice_id="INV-103", subtotal_cents=1250, status="paid")
        self.assertEqual(format_invoice_summary(inv), "INV-103 [paid]: $12.50")


if __name__ == "__main__":
    unittest.main()
