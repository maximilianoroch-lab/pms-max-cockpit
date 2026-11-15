import unittest
import pandas as pd
from pms_data_quality import history_status,suspicious_constant_quote

class DataQualityTests(unittest.TestCase):
    def test_missing_business_day_after_wednesday(self):
        status=history_status(["11/11/2026"],today="2026-11-14")
        self.assertEqual(status["business_days_missing"],2)
        self.assertEqual(status["last_observations"],1)
    def test_weekend_not_treated_as_trading_day(self):
        status=history_status(["13/11/2026"],today="2026-11-16")
        self.assertEqual(status["business_days_missing"],0)
    def test_empty_dates(self):
        self.assertIsNone(history_status([],today="2026-11-14")["latest"])
    def test_constant_price_discrepancy(self):
        data=pd.DataFrame([{"Ticker":"LLY","Fecha":str(day)+"/11/2026","Precio":"23100","Moneda":"ARS"} for day in [9,10,11]])
        finding=suspicious_constant_quote(data,"LLY",43100)
        self.assertEqual(finding["observations"],3)
        self.assertGreater(finding["difference_pct"],80)
    def test_no_false_alarm_when_quotes_move(self):
        data=pd.DataFrame([{"Ticker":"LLY","Fecha":str(day)+"/11/2026","Precio":str(price),"Moneda":"ARS"} for day,price in zip([9,10,11],[41000,42000,43000])])
        self.assertIsNone(suspicious_constant_quote(data,"LLY",43100))
if __name__=="__main__":unittest.main()
