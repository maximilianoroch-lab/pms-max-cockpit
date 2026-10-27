import unittest
import ast
from pathlib import Path

class BersochSimulatorIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
        cls.block=cls.source.split("def simulate_trade(",1)[1].split("COMPARISON_HELP=",1)[0]
    def test_app_syntax(self):
        ast.parse(self.source)
    def test_checks_cash_amount_finiteness(self):
        self.assertIn("not math.isfinite(cash_amount)",self.block)
        self.assertIn("cash_amount<0",self.block)
    def test_reconciles_result(self):
        self.assertIn("abs(sum(holdings.values())-new_total)>0.01",self.block)
        self.assertIn("not math.isfinite(new_total)",self.block)
        self.assertIn("any(not math.isfinite(v) for v in holdings.values())",self.block)
    def test_rejects_unknown_ticker(self):
        self.assertIn('ticker not in holdings or ticker=="CASH"',self.block)

if __name__=="__main__": unittest.main()
