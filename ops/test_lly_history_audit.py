import unittest
from ops.lly_history_audit import audit_history, price_number

REF = [
 {"date":"2026-11-11","ticker":"LLY","price_ars":"42800",
  "source":"reference", "settlement":"unverified","verification":"REFERENCE_ONLY"}
]


class ReadOnlyLLYTests(unittest.TestCase):
    def test_ars_thousands_formats(self):
        self.assertEqual(price_number("23.100"),23100)
        self.assertEqual(price_number("23.100,00"),23100)
        self.assertEqual(price_number("42,800.00"),42800)

    def test_detects_suspect_price_without_changing_history(self):
        rows=[{"Fecha":"11/11/2026","Ticker":"LLY","Precio":"23.100","Moneda":"ARS"}]
        original=[dict(x) for x in rows]
        report=audit_history(rows,REF)
        self.assertEqual(rows, original)
        self.assertFalse(report["reference_certified"])
        self.assertEqual(report["issues"][0]["status"],"SUSPECT_NOT_CERTIFIED")
        self.assertEqual(report["issues"][0]["historic_ars"],23100)

    def test_no_dated_reference_cannot_validate_another_day(self):
        rows=[{"Fecha":"12/11/2026","Ticker":"LLY","Precio":"23.100","Moneda":"ARS"}]
        self.assertEqual(audit_history(rows,REF)["issues"][0]["status"],"NO_DATED_REFERENCE")

    def test_other_currency_never_compared(self):
        rows=[{"Fecha":"11/11/2026","Ticker":"LLY","Precio":"100","Moneda":"USD"}]
        self.assertEqual(audit_history(rows,REF)["issues"][0]["status"],"NOT_COMPARABLE_CURRENCY")

    def test_duplicate_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicada"):
            audit_history([],REF+REF)

    def test_no_automatic_correction(self):
        rows=[{"Fecha":"11/11/2026","Ticker":"LLY","Precio":"42.800","Moneda":"ARS"}]
        report=audit_history(rows,REF)
        self.assertEqual(report["issues"],[])
        self.assertTrue(report["no_automatic_correction"])


if __name__ == "__main__":
    unittest.main()
