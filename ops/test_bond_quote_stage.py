import unittest
from datetime import date
from bond_quote_stage import usd_per_vn,stage
from bond_valuation_gate import EXPECTED

class TestBondStage(unittest.TestCase):
    def test_conversion(self):
        self.assertAlmostEqual(usd_per_vn(120000,1500),0.8)
    def test_no_zero_exchange_rate(self):
        with self.assertRaises(ValueError): usd_per_vn(120000,0)
    def test_unverified_cannot_stage(self):
        rows=[{"ticker":t,"unit":"UNVERIFIED","currency":"UNVERIFIED"} for t in EXPECTED]
        report=stage({"quotes":rows},fx=None,today=date(2026,10,21))
        self.assertFalse(report["ready"])
        self.assertEqual(report["rows"],[])
if __name__=="__main__":unittest.main()
