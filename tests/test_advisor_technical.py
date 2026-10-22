"""Pruebas sin API ni cotizaciones: seguridad del contexto del Asesor IA."""
import unittest
from advisor import eligible_technical_snapshot, describe_technical_snapshot

SNAP={
 "symbol":"AAPL","as_of":"2026-10-21","close_adjusted":250,
 "ema21":245,"ema50":230,"ema200":200,"rsi14":64
}

class TechnicalContextTests(unittest.TestCase):
 def test_active_ticker_matches(self):
  self.assertTrue(eligible_technical_snapshot(SNAP,"AAPL",["AAPL"]))
 def test_different_selected_ticker_rejected(self):
  self.assertFalse(eligible_technical_snapshot(SNAP,"MSFT",["AAPL","MSFT"]))
 def test_active_ticker_not_same_as_question_rejected(self):
  self.assertFalse(eligible_technical_snapshot(SNAP,"AAPL",["MSFT"]))
 def test_sole_mentioned_ticker_allowed(self):
  self.assertTrue(eligible_technical_snapshot(SNAP,"",["AAPL"]))
 def test_multiple_mentions_without_selection_rejected(self):
  self.assertFalse(eligible_technical_snapshot(SNAP,"",["AAPL","MSFT"]))
 def test_unrelated_chat_rejected(self):
  self.assertFalse(eligible_technical_snapshot(SNAP,"",[]))
 def test_missing_date_rejected(self):
  self.assertFalse(eligible_technical_snapshot({**SNAP,"as_of":""},"AAPL",[]))
 def test_ema_rsi_deterministic(self):
  x=describe_technical_snapshot(SNAP)
  self.assertEqual(x["quality"],"OK")
  self.assertEqual(x["price_vs_ema200_pct"],25)
  self.assertEqual(x["rsi14"],64)
 def test_invalid_rsi_not_reported_as_signal(self):
  self.assertEqual(describe_technical_snapshot({**SNAP,"rsi14":120})["quality"],"INDICADORES_INVALIDOS")
 def test_incomplete_indicators(self):
  self.assertEqual(describe_technical_snapshot({"close_adjusted":1})["quality"],"INDICADORES_INCOMPLETOS")

if __name__=="__main__":
 unittest.main()
