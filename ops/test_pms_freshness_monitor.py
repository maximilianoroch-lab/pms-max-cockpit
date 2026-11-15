import datetime as dt
import unittest
from ops.pms_freshness_monitor import assess_snapshots,assess_integrity,prior_business_date,parse_date

class FreshnessTests(unittest.TestCase):
    def test_prior_weekday_saturday(self):
        self.assertEqual(prior_business_date(dt.date(2026,11,14)),dt.date(2026,11,13))
    def test_prior_weekday_monday(self):
        self.assertEqual(prior_business_date(dt.date(2026,11,16)),dt.date(2026,11,13))
    def test_source_date_formats(self):
        self.assertEqual(parse_date("11/11/2026"),dt.date(2026,11,11))
        self.assertEqual(parse_date("2026-11-11"),dt.date(2026,11,11))
    def test_late_11nov_on_saturday(self):
        result=assess_snapshots([{"Fecha":"11/11/2026"}],dt.date(2026,11,14))
        self.assertEqual(result["status"],"LATE")
        self.assertEqual(result["missing_weekdays"],2)
    def test_valid_friday_close_saturday(self):
        result=assess_snapshots([{"Fecha":"13/11/2026"}],dt.date(2026,11,14))
        self.assertEqual(result["status"],"OK")
    def test_missing_control_is_not_silently_ok(self):
        rows=[{"Control":"Snapshot apto","Estado":"APTO"}]
        self.assertEqual(len(assess_integrity(rows)),2)
    def test_integrity_apto_requires_zero_gaps(self):
        rows=[{"Control":"Posiciones sin valor","Valor":"0"},
              {"Control":"Caja conciliación USD","Valor":"0"},
              {"Control":"Snapshot apto","Estado":"APTO"}]
        self.assertEqual(assess_integrity(rows),[])

if __name__=="__main__":unittest.main()
