"""Regression checks for automatic chart and selectable time window."""
import ast
import pathlib
import unittest

APP=pathlib.Path(__file__).resolve().parents[1]/"app.py"

class AdvisorChartWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=APP.read_text(encoding="utf-8")
        ast.parse(cls.code,filename=str(APP))
        start=cls.code.index('with st.expander("Análisis técnico')
        end=cls.code.index('    st.subheader("Asesor IA")',start)
        cls.chart=cls.code[start:end]

    def test_history_load_is_not_click_gated(self):
        chart=self.chart
        self.assertIn('if current_symbol and (current_symbol!=loaded_symbol or retry):',chart)
        self.assertIn('st.session_state["technical_data"]=_cached_technical_history(current_symbol)',chart)
        self.assertNotIn('if st.button("Consultar precios e indicadores"',chart)

    def test_time_windows_filter_locally(self):
        chart=self.chart
        self.assertIn('["6M","1A","3A","5A"]',chart)
        self.assertIn('shown=technical_data.loc[technical_data.index>=cut]',chart)

    def test_symbol_change_discards_stale_snapshot(self):
        chart=self.chart
        self.assertIn('st.session_state.pop("technical_snapshot",None)',chart)
        self.assertIn('current_symbol!=loaded_symbol',chart)

    def test_portfolio_ticker_selection_sync(self):
        self.assertIn('st.session_state["_technical_last_active_ticker"]=symbol_default',self.chart)
        self.assertIn('st.session_state["technical_symbol"]=symbol_default',self.chart)

if __name__=="__main__":
    unittest.main()
