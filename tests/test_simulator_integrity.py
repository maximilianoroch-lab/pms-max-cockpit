import ast
import unittest
from pathlib import Path
from pms_trade import simulate_portfolio_trade

class BersochSimulatorIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
    def test_app_syntax(self):
        ast.parse(self.source)
    def test_shared_engine_is_wired(self):
        self.assertIn("from pms_trade import simulate_portfolio_trade",self.source)
    def test_cash_funding_keeps_nav(self):
        r=simulate_portfolio_trade({"AAPL":1000,"CASH":500},"AAPL","Comprar",200,"CASH")
        self.assertEqual(r["total_after"],1500)
        self.assertEqual(r["cash_after"],300)
        self.assertEqual(r["funding_mode"],"CASH")
    def test_sale_overdraft_is_rejected(self):
        r=simulate_portfolio_trade({"AAPL":1000,"CASH":500},"AAPL","Vender",1001,"CASH")
        self.assertIn("error",r)
    def test_external_contribution_changes_nav(self):
        r=simulate_portfolio_trade({"AAPL":1000,"CASH":500},"AAPL","Comprar",200,"Aporte externo")
        self.assertEqual(r["total_after"],1700)
    def test_invalid_amount_is_rejected(self):
        r=simulate_portfolio_trade({"AAPL":1000,"CASH":500},"AAPL","Comprar",float("nan"),"CASH")
        self.assertIn("error",r)
if __name__=="__main__":unittest.main()
