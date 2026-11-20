import pathlib
import unittest

class ToolsNavigationPlaceholderTests(unittest.TestCase):
    def test_dashboard_uses_clear_tools_placeholder(self):
        text=pathlib.Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
        self.assertIn('TOOLS_PLACEHOLDER = "Elegir herramienta"',text)
        self.assertIn('[TOOLS_PLACEHOLDER,"Comparar Activos","Simular Compra/Venta"]',text)
        self.assertIn('if tool_page!=TOOLS_PLACEHOLDER:',text)
        self.assertIn('st.session_state.update(tools_nav=TOOLS_PLACEHOLDER)',text)
        self.assertNotIn('["—","Comparar Activos","Simular Compra/Venta"]',text)
    def test_ticker_no_selection_remains_distinct(self):
        text=pathlib.Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
        self.assertIn('ticker_options=["—"]+all_tickers',text)
        self.assertIn('st.session_state["active_ticker"]="" if selected_ticker=="—"',text)

if __name__=="__main__":
    unittest.main()
