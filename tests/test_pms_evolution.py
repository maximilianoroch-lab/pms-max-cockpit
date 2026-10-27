import unittest
import pandas as pd
from pms_evolution import observed_window
class ObservedWindowTests(unittest.TestCase):
 def setUp(self):
  self.data=pd.DataFrame({"Fecha":pd.to_datetime(["2025-01-01","2026-01-01","2026-10-01","2026-10-27"]),"Patrimonio USD":[10,20,30,40]})
 def test_all_preserves_observations(self):
  self.assertEqual(len(observed_window(self.data,"Fecha")),4)
 def test_short_period_does_not_invent_points(self):
  self.assertEqual(len(observed_window(self.data,"Fecha","1M")),2)
 def test_long_period_keeps_all_available(self):
  self.assertEqual(len(observed_window(self.data,"Fecha","5A")),4)
 def test_unknown_window_rejected(self):
  with self.assertRaises(ValueError):observed_window(self.data,"Fecha","6 años")
 def test_duplicate_date_keeps_last(self):
  more=pd.concat([self.data,self.data.iloc[[-1]].assign(**{"Patrimonio USD":99})],ignore_index=True)
  self.assertEqual(observed_window(more,"Fecha").iloc[-1]["Patrimonio USD"],99)
if __name__=="__main__":unittest.main()
