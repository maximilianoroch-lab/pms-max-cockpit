import unittest
import pandas as pd
from pms_compare import compare_portfolio_positions

class PortfolioComparisonTests(unittest.TestCase):
    def setUp(self):
        self.positions=pd.DataFrame({
            "Ticker":["AAPL","AAPL","SPY","CASH"],
            "Tipo":["Cedear","Cedear","ETF","Cash"],
            "Cantidad":[2,3,4,100],
            "Valor USD_num":[20,30,80,100]})
    def test_aggregates_multiple_accounts(self):
        result=compare_portfolio_positions(self.positions,"aapl","SPY")
        row=result.set_index("Ticker").loc["AAPL"]
        self.assertEqual(row["Valor USD"],50)
        self.assertEqual(row["Cantidad"],5)
        self.assertAlmostEqual(row["Peso cartera"],50/230)
        self.assertEqual(row["Tipo"],"Cedear")
    def test_does_not_mix_external_portfolio(self):
        result=compare_portfolio_positions(self.positions,"AAPL","SPY")
        self.assertEqual(set(result["Ticker"]),{"AAPL","SPY"})
    def test_rejects_same_or_missing_instrument(self):
        for a,b in [("AAPL","AAPL"),("aapl","AAPL"),("AAPL","TSLA")]:
            with self.assertRaises(ValueError):
                compare_portfolio_positions(self.positions,a,b)
    def test_rejects_invalid_valuation(self):
        bad=self.positions.copy()
        bad.loc[0,"Valor USD_num"]=-2
        with self.assertRaises(ValueError):
            compare_portfolio_positions(bad,"AAPL","SPY")
    def test_rejects_infinite_valuation(self):
        invalid=self.positions.copy()
        invalid["Valor USD_num"]=invalid["Valor USD_num"].astype(float)
        invalid.loc[0,"Valor USD_num"]=float("inf")
        with self.assertRaises(ValueError):
            compare_portfolio_positions(invalid,"AAPL","SPY")
    def test_bersoch_quantity_num_column(self):
        x=self.positions.rename(columns={"Cantidad":"Cantidad_num"})
        got=compare_portfolio_positions(x,"AAPL","SPY")
        self.assertEqual(got.set_index("Ticker").loc["AAPL","Cantidad"],5)
    def test_missing_quantity_not_invented(self):
        x=self.positions.drop(columns=["Cantidad"])
        got=compare_portfolio_positions(x,"AAPL","SPY")
        self.assertNotIn("Cantidad",got.columns)
    def test_rejects_total_smaller_than_holdings(self):
        with self.assertRaises(ValueError):
            compare_portfolio_positions(self.positions,"AAPL","SPY",100)
if __name__=="__main__":unittest.main()
