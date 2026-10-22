"""Pruebas sin datos privados, reproducibles en ambos escritorios."""
import unittest
import pandas as pd
from presentation_format import fmt_usd, fmt_num, fmt_pct, pct_points, table_money, local_num, compact_status

class FormatTests(unittest.TestCase):
    def test_usd(self):
        self.assertEqual(fmt_usd(1234567.2),"US$ 1.234.567")
        self.assertEqual(fmt_num(1234.56,2),"1.234,56")
        self.assertEqual(fmt_pct(.253,1),"25,3%")
    def test_source_unchanged(self):
        df=pd.DataFrame({"Valor USD_num":[1000.0],"Peso_num":[.25]})
        out=table_money(df)
        self.assertEqual(out["Valor USD_num"].iloc[0],"US$ 1.000")
        self.assertEqual(df["Valor USD_num"].iloc[0],1000.0)
        self.assertEqual(float(pct_points(df["Peso_num"]).iloc[0]),25.0)
    def test_parsing_and_status(self):
        self.assertEqual(local_num("1.234,50"),1234.5)
        self.assertEqual(compact_status("ACTUALIZADO"),"Actualizado")
if __name__=="__main__":
    unittest.main()
