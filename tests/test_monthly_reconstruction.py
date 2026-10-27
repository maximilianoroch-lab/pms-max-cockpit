import unittest
import pandas as pd
from monthly_reconstruction import monthly_quantities

class MonthlyHistoryTest(unittest.TestCase):
    def test_cumulative_quantities(self):
        source=pd.DataFrame({
            "Fecha":["2024-01-10","2024-02-03","2024-03-05","2024-03-07"],
            "Evento":["Compra","Compra","Venta","Interés"],
            "Ticker":["ABC","ABC","ABC","ABC"],
            "Tipo":["ETF"]*4,
            "Cantidad":[10,5,-3,0]
        })
        out,issues=monthly_quantities(source)
        result=out.set_index("Mes")["Cantidad"].to_dict()
        self.assertEqual(result,{"2024-01":10,"2024-02":15,"2024-03":12})
        self.assertTrue(issues.empty)

    def test_options_are_exceptions_not_shares(self):
        source=pd.DataFrame({"Fecha":[45292,45292],"Evento":["Compra","Call"],"Ticker":["ABC","ABC"],
                             "Tipo":["Cedear","Opciones"],"Cantidad":[10,100]})
        out,issues=monthly_quantities(source)
        self.assertEqual(float(out["Cantidad"].sum()),10)
        self.assertEqual(int(issues["Eventos sin conciliación"].sum()),1)

if __name__=="__main__":
    unittest.main()
