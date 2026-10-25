import unittest
from pathlib import Path

class VisibleTypeOnly(unittest.TestCase):
    def test_class_not_rendered_in_positions_or_custody(self):
        app=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
        self.assertNotIn('"Tipo","Clase","Cantidad_num"',app)
        self.assertNotIn('"Cuenta","Clase","Tipo","Región directa"',app)
        self.assertNotIn('snap["Clase"]} · {snap["Tipo"]',app)
        self.assertNotIn('classes=source["Clase"]',app)
        self.assertNotIn('"Clase":"Clase"',app)
        self.assertIn('tickers.eq("GLD")',app)
    def test_type_remains_available(self):
        app=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
        self.assertIn('"Custodio":"Custodio","Tipo":"Tipo"',app)

if __name__=="__main__":unittest.main()
