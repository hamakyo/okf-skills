import unittest

from src.invoices import Invoice
from src.storage import InMemoryInvoiceStore


class StorageTests(unittest.TestCase):
    def test_add_get_and_list_invoices(self) -> None:
        store = InMemoryInvoiceStore()
        inv = Invoice(invoice_id="INV-1", subtotal_cents=500)
        store.add_invoice(inv)
        self.assertEqual(store.get_invoice("INV-1"), inv)
        self.assertEqual(store.list_invoices(), [inv])


if __name__ == "__main__":
    unittest.main()
