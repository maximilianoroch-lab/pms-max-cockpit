import unittest
import pandas as pd
from monthly_type_history import monthly_type_values,TYPES

class MonthlyTypesTests(unittest.TestCase):
 def test_five_values_are_in_thousands(self):
  d=pd.DataFrame({"Fecha":["2026-09-30"]*5,"Ticker":["C","E","D","B","A"],
    "Tipo":list(TYPES),"Valor USD":[1000,2000,3000,4000,5000]})
  r=monthly_type_values(d,expected_tickers=["C","E","D","B","A"])
  self.assertEqual(r.iloc[0]["Estado"],"OBSERVADO")
  self.assertEqual([r.iloc[0][t] for t in TYPES],[1,2,3,4,5])
 def test_missing_position_makes_month_incomplete(self):
  d=pd.DataFrame({"Fecha":["2026-09-30"],"Ticker":["E"],"Tipo":["ETF"],"Valor USD":[2000]})
  r=monthly_type_values(d,expected_tickers=["E","D"])
  self.assertEqual(r.iloc[0]["Estado"],"INCOMPLETO")
  self.assertTrue(pd.isna(r.iloc[0]["ETF"]))
 def test_uses_only_latest_date_in_month(self):
  d=pd.DataFrame({"Fecha":["2026-09-15","2026-09-30"],"Ticker":["E","E"],
    "Tipo":["ETF","ETF"],"Valor USD":[1000,3000]})
  r=monthly_type_values(d)
  self.assertEqual(r.iloc[0]["ETF"],3.0)

if __name__=="__main__":
 unittest.main()
