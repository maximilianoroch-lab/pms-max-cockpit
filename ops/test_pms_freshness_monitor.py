import datetime as dt
import unittest
import tempfile
import pathlib
from ops.pms_freshness_monitor import assess_snapshots,assess_integrity,prior_business_date,parse_date,load_market_holidays

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

    def test_calendar_skips_friday_holiday(self):
        holidays={dt.date(2026,11,13)}
        self.assertEqual(prior_business_date(dt.date(2026,11,14), holidays),
                         dt.date(2026,11,12))
        result=assess_snapshots([{"Fecha":"12/11/2026"}],
                                dt.date(2026,11,14), holidays)
        self.assertEqual(result["status"],"OK")
        self.assertEqual(result["missing_weekdays"],0)

    def test_calendar_excludes_holiday_from_missing_count(self):
        holidays={dt.date(2026,11,12)}
        result=assess_snapshots([{"Fecha":"11/11/2026"}],
                                dt.date(2026,11,14), holidays)
        self.assertEqual(result["status"],"LATE")
        self.assertEqual(result["missing_weekdays"],1)

    def test_load_calendar_rejects_invalid_date(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory)/"holidays.csv"
            p.write_text("date,source\n2026-13-40,invalid\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_market_holidays(str(p))

    def test_load_calendar_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory)/"holidays.csv"
            p.write_text("date,source\n2026-11-13,verified exchange notice\n", encoding="utf-8")
            self.assertIn(dt.date(2026,11,13),load_market_holidays(str(p)))

    def test_official_byma_2026_calendar_treats_trading_without_settlement_as_open(self):
        from pathlib import Path
        holidays=load_market_holidays(str(Path(__file__).parent/"byma_no_trading_2026.csv"))
        self.assertIn(dt.date(2026,11,9),holidays)
        self.assertIn(dt.date(2026,11,10),holidays)
        self.assertNotIn(dt.date(2026,11,6),holidays)
        self.assertNotIn(dt.date(2026,12,24),holidays)
        self.assertNotIn(dt.date(2026,11,12),holidays)
        self.assertNotIn(dt.date(2026,11,13),holidays)
        self.assertEqual(prior_business_date(dt.date(2026,11,11),holidays),
                         dt.date(2026,11,6))
        self.assertEqual(prior_business_date(dt.date(2026,11,14),holidays),
                         dt.date(2026,11,13))

if __name__=="__main__":unittest.main()
