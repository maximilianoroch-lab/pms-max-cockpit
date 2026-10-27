import unittest
from ops.data912_monthly_audit import month_closes,fetch_ticker

class Data912AuditTests(unittest.TestCase):
    def test_latest_trading_day_per_month(self):
        sample=[{"date":"2024-01-29","c":10},{"date":"2024-01-31","c":12},
                {"date":"2024-02-27","c":15},{"date":"2023-12-29","c":99},
                {"date":"2024-02-28","c":None}]
        rows=month_closes(sample,"GGAL","Acción AR")
        self.assertEqual([(r["mes"],r["cierre_ars"]) for r in rows],
                         [("2024-01",12.0),("2024-02",15.0)])
    def test_unsupported_is_not_valued(self):
        class NoNetwork:
            def get(self,*a,**k): raise AssertionError("no network")
        rows,status=fetch_ticker(NoNetwork(),"BTC","Cripto")
        self.assertEqual(rows,[])
        self.assertEqual(status,"NO_CUBIERTO")

if __name__=="__main__":
    unittest.main()
