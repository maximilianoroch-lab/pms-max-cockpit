import unittest
from ops.snapshot_coverage_preflight import audit_snapshot_coverage


class SnapshotCoveragePreflightTests(unittest.TestCase):
    def positions(self):
        return [
            {"Fecha":"2026-11-12","Ticker":"AAPL","Cantidad":"1"},
            {"Fecha":"2026-11-12","Ticker":"LLY","Cantidad":"2"},
            {"Fecha":"2026-11-13","Ticker":"AAPL","Cantidad":"1"},
            {"Fecha":"2026-11-13","Ticker":"LLY","Cantidad":"2"}
        ]
    def quotes(self):
        return [
            {"Fecha":"2026-11-12","Ticker":"AAPL","Precio":"150","Moneda":"USD","Fuente":"dated provider","Corte":"17:00"},
            {"Fecha":"2026-11-13","Ticker":"LLY","Precio":"43100","Moneda":"ARS","Fuente":"dated provider","Corte":"17:00"}
        ]
    def test_partial_quote_coverage_does_not_certify(self):
        result=audit_snapshot_coverage(self.positions(),self.quotes(),["2026-11-12","2026-11-13"])
        self.assertFalse(result["cierre_certificado"])
        self.assertEqual(result["fechas"][0]["faltantes"],["LLY"])
        self.assertEqual(result["fechas"][1]["faltantes"],["AAPL"])
    def test_no_positions_does_not_count_as_complete(self):
        result=audit_snapshot_coverage([],self.quotes(),["2026-11-12"])
        self.assertEqual(result["fechas"][0]["estado"],"FALTAN_TENENCIAS_FECHADAS")
    def test_valid_quotes_are_still_only_preliminary(self):
        quotes=self.quotes()+[
            {"Fecha":"2026-11-12","Ticker":"LLY","Precio":"42820","Moneda":"ARS","Fuente":"dated","Corte":"17:00"},
            {"Fecha":"2026-11-13","Ticker":"AAPL","Precio":"160","Moneda":"USD","Fuente":"dated","Corte":"17:00"}]
        result=audit_snapshot_coverage(self.positions(),quotes,["2026-11-12","2026-11-13"])
        self.assertTrue(all(day["estado"]=="COBERTURA_PRELIMINAR_COMPLETA" for day in result["fechas"]))
        self.assertFalse(result["cierre_certificado"])
    def test_missing_provenance_remains_missing(self):
        quotes=self.quotes()
        quotes[0]["Fuente"]=""
        result=audit_snapshot_coverage(self.positions(),quotes,["2026-11-12"])
        self.assertEqual(result["fechas"][0]["faltantes"],["AAPL","LLY"])
    def test_reject_duplicate_holdings(self):
        positions=self.positions()
        with self.assertRaisesRegex(ValueError,"duplicada"):
            audit_snapshot_coverage(positions+[positions[0]],self.quotes(),["2026-11-12"])
    def test_reject_duplicate_quotes(self):
        quotes=self.quotes()
        with self.assertRaisesRegex(ValueError,"duplicada"):
            audit_snapshot_coverage(self.positions(),quotes+[quotes[0]],["2026-11-12"])


if __name__=="__main__":
    unittest.main()
