from datetime import date
import unittest
from bond_quote_validation import validate_bond_quote, value_usd, BondQuoteError

GOOD = dict(symbol="GD35", market="BYMA", currency="ARS", nominal_basis=100,
            price=85000, market_date="2026-10-21", source="Proveedor autorizado")

class TestBondValuation(unittest.TestCase):
    def test_ars_100_vn(self):
        self.assertEqual(value_usd(200, GOOD, usd_fx=1000, today=date(2026,10,22)),170)
    def test_usd_100_vn(self):
        q=dict(GOOD,currency="USD",price=70)
        self.assertEqual(value_usd(200,q,today=date(2026,10,22)),140)
    def test_no_unit(self):
        with self.assertRaises(BondQuoteError):
            validate_bond_quote(dict(GOOD,nominal_basis=None),today=date(2026,10,22))
    def test_stale(self):
        with self.assertRaises(BondQuoteError):
            validate_bond_quote(dict(GOOD,market_date="2026-09-01"),today=date(2026,10,22))
    def test_no_currency(self):
        with self.assertRaises(BondQuoteError):
            validate_bond_quote(dict(GOOD,currency=""),today=date(2026,10,22))
    def test_invalid_price(self):
        with self.assertRaises(BondQuoteError):
            validate_bond_quote(dict(GOOD,price=-4),today=date(2026,10,22))

if __name__ == "__main__":
    unittest.main()
