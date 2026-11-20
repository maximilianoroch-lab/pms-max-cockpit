import csv
import pathlib
import unittest
from datetime import date

ROOT=pathlib.Path(__file__).resolve().parents[1]

class PublicETFSafetyTests(unittest.TestCase):
    def test_public_repo_has_no_issuer_holdings_distribution(self):
        self.assertFalse((ROOT/"etf_top_holdings.csv").exists(),
                         "Public repo must not publish issuer positions without rights review")
    def test_sources_are_metadata_only_and_not_marked_approved(self):
        with (ROOT/"ops/etf_sources_registry.csv").open(encoding="utf-8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),7)
        self.assertEqual(set(x["ETF"] for x in rows),
                         {"SPY","QQQ","XLV","ACWI","FXI","EEM","EWZ"})
        for row in rows:
            self.assertEqual(row["Estado"],"PENDIENTE_LICENCIA")
            self.assertTrue(row["Referencia"].startswith("https://"))
            date.fromisoformat(row["Fecha_fuente"])
            self.assertEqual(set(row),{"ETF","Emisor","Fecha_fuente","Referencia","Estado"})

if __name__=="__main__":
    unittest.main()
