"""Fast partial ETF look-through, deliberately never treating the uncovered balance as zero risk.

Input holdings: ETF, Constituyente, Peso ETF (fraction), Fuente, Fecha.
Only top holdings with a source/date should be supplied; the rest remains 'no desagregado'.
"""
import math
import pandas as pd

def approximate_etf_overlap(positions,top_holdings,max_names=10):
    """USD of direct and sourced ETF exposure by underlying ticker.

    Deliberately does not infer ETF sector or geography from an unsourced constituent.
    """
    if max_names<1:raise ValueError("max_names inválido")
    if positions is None or positions.empty or top_holdings is None or top_holdings.empty:
        return pd.DataFrame(columns=["Activo","Directo USD","ETF parcial USD","Total identificado USD"]),pd.DataFrame(columns=["ETF","Cobertura","Sin desagregar"])
    required_pos={"Ticker","Valor USD_num"}
    required_etf={"ETF","Constituyente","Peso ETF","Fuente","Fecha"}
    if not required_pos.issubset(positions) or not required_etf.issubset(top_holdings):
        raise ValueError("Columnas insuficientes")
    pos=positions.copy();pos["Ticker"]=pos["Ticker"].astype(str).str.strip().str.upper()
    pos["Valor USD_num"]=pd.to_numeric(pos["Valor USD_num"],errors="raise")
    if not pos["Valor USD_num"].map(math.isfinite).all() or (pos["Valor USD_num"]<0).any():
        raise ValueError("Posiciones inválidas")
    holdings=top_holdings.copy()
    holdings["ETF"]=holdings["ETF"].astype(str).str.upper().str.strip()
    holdings["Constituyente"]=holdings["Constituyente"].astype(str).str.upper().str.strip()
    holdings["Peso ETF"]=pd.to_numeric(holdings["Peso ETF"],errors="raise")
    if (holdings["Peso ETF"]<0).any() or (holdings["Peso ETF"]>1).any() or not holdings["Peso ETF"].map(math.isfinite).all():
        raise ValueError("Pesos ETF inválidos")
    if holdings[["ETF","Constituyente"]].duplicated().any() or holdings["Fuente"].isna().any() or holdings["Fecha"].isna().any() or (holdings["Fuente"].astype(str).str.strip()=="").any():
        raise ValueError("Composición sin fuente, fecha o con ticker duplicado")
    holdings=holdings.sort_values(["ETF","Peso ETF"],ascending=[True,False]).groupby("ETF",group_keys=False).head(max_names)
    exposure=pos.groupby("Ticker")["Valor USD_num"].sum()
    rows=[];coverage=[]
    for etf,part in holdings.groupby("ETF"):
        if etf not in exposure:continue
        weight=float(part["Peso ETF"].sum())
        if weight>1.000001:raise ValueError("Cobertura ETF superior a 100%")
        value=float(exposure[etf])
        coverage.append({"ETF":etf,"Cobertura":weight,"Sin desagregar":max(0,1-weight),"Valor sin desagregar USD":value*max(0,1-weight)})
        for _,r in part.iterrows():
            rows.append({"Activo":r["Constituyente"],"ETF parcial USD":value*r["Peso ETF"]})
    indirect=pd.DataFrame(rows).groupby("Activo",as_index=False)["ETF parcial USD"].sum() if rows else pd.DataFrame(columns=["Activo","ETF parcial USD"])
    # Only identified underlyings: ETF wrappers, cash and unrelated assets
    # must not be added as if they were distinct underlying exposure.
    direct=indirect[["Activo"]].copy()
    direct["Directo USD"]=direct["Activo"].map(exposure).fillna(0.0)
    both=direct.merge(indirect,on="Activo",how="left")
    both["Total identificado USD"]=both["Directo USD"]+both["ETF parcial USD"]
    return both.sort_values("Total identificado USD",ascending=False),pd.DataFrame(coverage)
