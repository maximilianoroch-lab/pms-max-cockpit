import unittest
import pandas as pd
from technical import indicators

class TestTechnical(unittest.TestCase):
    def test_indicators_ranges(self):
        s=pd.Series([100+i*0.3 for i in range(250)])
        out=indicators(s)
        self.assertEqual(len(out),250)
        self.assertTrue(0<=out["RSI 14"].iloc[-1]<=100)
        self.assertTrue(out["EMA 21"].iloc[-1]>out["EMA 200"].iloc[-1])
    def test_insufficient_history(self):
        with self.assertRaises(ValueError):
            indicators([100]*30)

if __name__=="__main__":
    unittest.main()
