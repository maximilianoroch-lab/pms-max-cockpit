"""Pruebas de regresión del ranking de cotizaciones; ejecutar: python -m unittest discover -s tests."""
import unittest
from unittest.mock import patch
import pandas as pd
from pms_movers import rank_movers

def row(fecha,ticker,precio,moneda="ARS",usd="1"):
    return {"Fecha":fecha,"Ticker":ticker,"Precio":str(precio),"Moneda":moneda,"Precio USD":str(usd)}

class RankingPesosTests(unittest.TestCase):
    def check(self,rows,tickers):
        with patch("pms_movers._history",return_value=pd.DataFrame(rows)):
            return rank_movers("ficticio",tickers)

    def test_viernes_a_martes_con_feriado(self):
        rows=[row("06/11/2026","AAA",100),row("10/11/2026","AAA",110),
              row("06/11/2026","BBB",200),row("10/11/2026","BBB",190)]
        got,date=self.check(rows,["AAA","BBB"])
        self.assertEqual(date.strftime("%Y-%m-%d"),"2026-11-10")
        self.assertAlmostEqual(got.set_index("Activo").loc["AAA","Diaria %"],10)
        self.assertAlmostEqual(got.set_index("Activo").loc["BBB","Diaria %"],-5)

    def test_cierre_mensual_vs_ultima_rueda_mes_anterior(self):
        rows=[row("29/10/2026","AAA",90),row("30/10/2026","AAA",100),
              row("10/11/2026","AAA",105),row("11/11/2026","AAA",110)]
        got,_=self.check(rows,["AAA"])
        one=got.iloc[0]
        self.assertAlmostEqual(one["Diaria %"],(110/105-1)*100)
        self.assertAlmostEqual(one["Mes %"],10)

    def test_mes_sin_base_no_inventa_cero(self):
        rows=[row("10/11/2026","AAA",100),row("11/11/2026","AAA",105)]
        got,_=self.check(rows,["AAA"])
        self.assertIsNone(got.iloc[0]["Mes %"])

    def test_no_compara_tickers_con_fechas_desfasadas(self):
        rows=[row("10/11/2026","AAA",100),row("11/11/2026","AAA",110),
              row("09/11/2026","BBB",100),row("10/11/2026","BBB",200)]
        got,date=self.check(rows,["AAA","BBB"])
        self.assertEqual(date.strftime("%Y-%m-%d"),"2026-11-11")
        self.assertEqual(got["Activo"].tolist(),["AAA"])

    def test_cripto_usd_a_pesos_misma_fecha(self):
        rows=[]
        for day,fx in [("10/11/2026",1500),("11/11/2026",1600)]:
            for t in ["AAA","BBB","CCC"]:
                rows.append(row(day,t,fx,"ARS","1"))
            rows.append(row(day,"BTC",100,"USD","100"))
        got,_=self.check(rows,["BTC","AAA","BBB","CCC"])
        btc=got.set_index("Activo").loc["BTC"]
        self.assertAlmostEqual(btc["Diaria %"],(1600/1500-1)*100)

if __name__=="__main__":
    unittest.main()
