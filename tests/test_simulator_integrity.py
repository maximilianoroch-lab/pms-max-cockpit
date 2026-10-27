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
    def test_sell_to_cash_preserves_nav(self):
        r=simulate_portfolio_trade({"AAPL":1000,"CASH":500},"AAPL","Vender",200,"CASH")
        self.assertEqual(r["total_after"],1500)
        self.assertEqual(r["cash_after"],700)
    def test_external_withdrawal_reduces_nav(self):
        r=simulate_portfolio_trade({"AAPL":1000,"CASH":500},"AAPL","Vender",200,"Retiro externo")
        self.assertEqual(r["total_after"],1300)
        self.assertEqual(r["cash_after"],500)
    def test_sale_funded_purchase_preserves_nav(self):
        r=simulate_portfolio_trade({"AAPL":1000,"SPY":2000,"CASH":500},"AAPL","Comprar",300,"Venta de otro activo","SPY")
        self.assertEqual(r["total_after"],3500)
        self.assertEqual(r["source_after"],1700)
    def test_combined_funding_preserves_nav(self):
        r=simulate_portfolio_trade({"AAPL":1000,"SPY":2000,"CASH":500},"AAPL","Comprar",300,"CASH + venta de activo","SPY",100)
        self.assertEqual(r["total_after"],3500)
        self.assertEqual(r["cash_after"],400)
        self.assertEqual(r["source_after"],1800)
    def test_input_positions_not_modified(self):
        holdings={"AAPL":1000,"SPY":2000,"CASH":500}
        simulate_portfolio_trade(holdings,"AAPL","Comprar",250,"CASH")
        self.assertEqual(holdings,{"AAPL":1000,"SPY":2000,"CASH":500})
    def test_invalid_amount_is_rejected(self):
        r=simulate_portfolio_trade({"AAPL":1000,"CASH":500},"AAPL","Comprar",float("nan"),"CASH")
        self.assertIn("error",r)
if __name__=="__main__":unittest.main()
