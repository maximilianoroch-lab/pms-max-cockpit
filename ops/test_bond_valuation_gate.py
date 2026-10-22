import unittest
from datetime import date
from bond_valuation_gate import assess,EXPECTED

class GateTests(unittest.TestCase):
    def test_unverified_never_promoted(self):
        rows=[{"ticker":t,"source":"https://iol.invertironline.com/Titulo/DatosHistoricos",
               "latest_row":{"market_date":"2026-10-21"},
               "currency":"UNVERIFIED","unit":"UNVERIFIED","valuation_eligible":False}
              for t in EXPECTED]
        report=assess({"quotes":rows},today=date(2026,10,21))
        self.assertFalse(report["safe_to_publish"])
        self.assertEqual(len(report["checks"]),6)
        self.assertTrue(all("UNIT_UNVERIFIED" in x["reasons"] for x in report["checks"]))
    def test_missing_bond_blocks(self):
        self.assertFalse(assess({"quotes":[]})["safe_to_publish"])
if __name__=="__main__":unittest.main()
