import unittest
from ops.snapshot_calendar_audit import audit_trading_dates

class CalendarSnapshotTests(unittest.TestCase):
    def test_byma_closed_dates_are_flagged_not_removed(self):
        rows=[
            {"Fecha":"9/11/2026","Fuente":"Automático PMS"},
            {"Fecha":"10/11/2026","Fuente":"Automático PMS"},
            {"Fecha":"11/11/2026","Fuente":"Automático PMS"}
        ]
        old=[dict(r) for r in rows]
        result=audit_trading_dates(rows,{"2026-11-09","2026-11-10"})
        self.assertEqual(len(result["alertas"]),2)
        self.assertEqual([x["fecha"] for x in result["alertas"]],
                         ["2026-11-09","2026-11-10"])
        self.assertEqual(rows,old)
        self.assertFalse(result["automatic_corrections"])

    def test_invalid_date_is_explicit(self):
        result=audit_trading_dates([{"Fecha":"not-a-date"}],set())
        self.assertEqual(result["alertas"][0]["status"],"FECHA_INVALIDA")

    def test_trading_without_settlement_is_not_flagged_as_closed(self):
        result=audit_trading_dates([{"Fecha":"06/11/2026"}],
                                   {"2026-11-09","2026-11-10"})
        self.assertEqual(result["alertas"],[])

if __name__=="__main__":
    unittest.main()
