import unittest
import pandas as pd
from pms_etf_overlap import approximate_etf_overlap
class PartialLookthrough(unittest.TestCase):
 def test_top_holdings_and_uncovered_balance(self):
  p=pd.DataFrame({"Ticker":["AAPL","SPY","CASH"],"Valor USD_num":[100,1000,50]})
  c=pd.DataFrame({"ETF":["SPY","SPY"],"Constituyente":["AAPL","MSFT"],"Peso ETF":[.06,.05],"Fuente":["issuer","issuer"],"Fecha":["2026-10-01","2026-10-01"]})
  combined,cover=approximate_etf_overlap(p,c)
  self.assertAlmostEqual(combined.set_index("Activo").loc["AAPL","Total identificado USD"],160)
  self.assertAlmostEqual(cover.iloc[0]["Sin desagregar"],.89)
 def test_etf_wrapper_not_double_counted_as_underlying(self):
  p=pd.DataFrame({"Ticker":["SPY","AAPL","CASH"],"Valor USD_num":[1000,100,50]})
  c=pd.DataFrame({"ETF":["SPY"],"Constituyente":["AAPL"],"Peso ETF":[.06],"Fuente":["issuer"],"Fecha":["2026-10-01"]})
  combined,coverage=approximate_etf_overlap(p,c)
  self.assertEqual(combined["Activo"].tolist(),["AAPL"])
  self.assertAlmostEqual(combined.iloc[0]["Directo USD"],100)
  self.assertAlmostEqual(combined.iloc[0]["ETF parcial USD"],60)
 def test_missing_composition_does_not_invent_exposure(self):
  p=pd.DataFrame({"Ticker":["AAPL"],"Valor USD_num":[100]})
  out,cov=approximate_etf_overlap(p,pd.DataFrame())
  self.assertTrue(out.empty)
 def test_over_full_coverage_rejected(self):
  p=pd.DataFrame({"Ticker":["SPY"],"Valor USD_num":[100]})
  c=pd.DataFrame({"ETF":["SPY","SPY"],"Constituyente":["A","B"],"Peso ETF":[.9,.8],"Fuente":["issuer","issuer"],"Fecha":["x","x"]})
  with self.assertRaises(ValueError):approximate_etf_overlap(p,c)
 def test_missing_source_rejected(self):
  p=pd.DataFrame({"Ticker":["SPY"],"Valor USD_num":[100]})
  c=pd.DataFrame({"ETF":["SPY"],"Constituyente":["A"],"Peso ETF":[.2],"Fuente":[""],"Fecha":["x"]})
  with self.assertRaises(ValueError):approximate_etf_overlap(p,c)
if __name__=="__main__":unittest.main()
