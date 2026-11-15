import unittest
import pandas as pd
from pms_etf_materiality import evaluate_etf_materiality

def sample():
    exposures=pd.DataFrame([
        {"Activo":"AAPL","Directo USD":500,"ETF parcial USD":2500,"Total identificado USD":3000},
        {"Activo":"MSFT","Directo USD":0,"ETF parcial USD":200,"Total identificado USD":200},
    ])
    coverage=pd.DataFrame([
        {"ETF":"SPY","Cobertura":.4,"Sin desagregar":.6,"Valor sin desagregar USD":3500}
    ])
    source=pd.DataFrame([{"ETF":"SPY","Fecha":"2026-11-05"}])
    return exposures,coverage,source

class ETFMaterialityPolicyTests(unittest.TestCase):
    def test_material_exposure_and_uncovered_balance(self):
        out=evaluate_etf_materiality(*sample(),portfolio_total_usd=100000,as_of="2026-11-15")
        types={r["tipo"] for r in out["hallazgos"]}
        self.assertEqual(types,{"EMISOR_IDENTIFICADO_PARCIAL","FRACCION_ETF_NO_DESAGREGADA_MATERIAL"})
        self.assertEqual(out["estado"],"PROPUESTA_NO_ACTIVADA")
        self.assertTrue(out["no_es_recomendacion"])

    def test_stale_source_always_flagged_separately(self):
        e,c,s=sample()
        s.loc[0,"Fecha"]="2026-09-01"
        out=evaluate_etf_materiality(e,c,s,100000,"2026-11-15")
        self.assertIn("ETF_COMPOSICION_ANTIGUA",{r["tipo"] for r in out["hallazgos"]})

    def test_missing_source_date_blocks_freshness_claim(self):
        e,c,_=sample()
        source=pd.DataFrame(columns=["ETF","Fecha"])
        out=evaluate_etf_materiality(e,c,source,100000,"2026-11-15")
        self.assertIn("ETF_SIN_FECHA_FUENTE",{r["tipo"] for r in out["hallazgos"]})

    def test_future_or_mixed_source_dates_rejected(self):
        e,c,s=sample();s.loc[0,"Fecha"]="2026-12-10"
        with self.assertRaisesRegex(ValueError,"futuro"):
            evaluate_etf_materiality(e,c,s,100000,"2026-11-15")
        s=pd.DataFrame([{"ETF":"SPY","Fecha":"2026-11-10"},{"ETF":"SPY","Fecha":"2026-11-11"}])
        with self.assertRaisesRegex(ValueError,"mixtas"):
            evaluate_etf_materiality(e,c,s,100000,"2026-11-15")

    def test_thresholds_and_total_fail_closed(self):
        e,c,s=sample()
        for total in (0,-1,float("nan")):
            with self.assertRaises(ValueError):
                evaluate_etf_materiality(e,c,s,total,"2026-11-15")
        with self.assertRaises(ValueError):
            evaluate_etf_materiality(e,c,s,100000,"2026-11-15",materiality_fraction=0)
        with self.assertRaises(ValueError):
            evaluate_etf_materiality(e,c,s,100000,"2026-11-15",max_source_age_days=-1)

if __name__=="__main__":
    unittest.main()
