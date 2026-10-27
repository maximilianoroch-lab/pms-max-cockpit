"""Provisional, clearly marked linear valuations for FUT, GALILEO and SCHROD.

Anchors: actual acquisition cost in USD and last *recorded* manual market value.
Interpolation is NOT a verified historical price or portfolio performance.
Observed month-end valuations, when available, always override projections.
"""
import calendar
import pandas as pd

SPECIAL_TYPES={"FUT":"Cripto","GALILEO":"ETF","SCHROD":"ETF"}

def _date(value):
    numeric=pd.to_numeric(pd.Series([value]),errors="coerce").iloc[0]
    if pd.notna(numeric):
        return pd.to_datetime(numeric,unit="D",origin="1899-12-30",errors="coerce")
    return pd.to_datetime(value,dayfirst=True,format="mixed",errors="coerce")

def provisional_monthly(operations, current_positions, observed=None):
    required_ops={"Ticker","Fecha","Evento","Flujo USD"}
    required_positions={"Ticker","Valor USD","Fecha dato"}
    if not required_ops.issubset(operations.columns) or not required_positions.issubset(current_positions.columns):
        raise ValueError("Faltan columnas necesarias para la proyección")
    observed=observed if observed is not None else pd.DataFrame()
    output=[]
    for ticker,group in operations.groupby(operations["Ticker"].astype(str).str.upper()):
        if ticker not in SPECIAL_TYPES:continue
        buys=group.loc[group["Evento"].astype(str).str.lower().eq("compra")].copy()
        if len(buys)!=1:continue  # Múltiples movimientos requieren metodología de lotes.
        buy=buys.iloc[0]
        start=_date(buy["Fecha"])
        cost=-pd.to_numeric(buy["Flujo USD"],errors="coerce")
        positions=current_positions.loc[current_positions["Ticker"].astype(str).str.upper().eq(ticker)]
        if len(positions)!=1:continue
        pos=positions.iloc[0]
        end=_date(pos["Fecha dato"])
        final=pd.to_numeric(pos["Valor USD"],errors="coerce")
        if pd.isna(start) or pd.isna(end) or pd.isna(cost) or pd.isna(final) or cost<0 or final<0 or end<=start:
            continue
        for period in pd.period_range(start.to_period("M"),end.to_period("M"),freq="M"):
            last=period.end_time.normalize()
            sample=min(last,end)
            if sample<start:continue
            observation=observed.loc[
                observed.get("Ticker",pd.Series(dtype=str)).astype(str).str.upper().eq(ticker)
                & observed.get("Mes",pd.Series(dtype=str)).astype(str).eq(str(period))
            ] if {"Ticker","Mes"}.issubset(observed.columns) else pd.DataFrame()
            if not observation.empty:
                val=pd.to_numeric(observation.iloc[-1].get("Valor USD"),errors="coerce")
                if pd.notna(val) and val>=0:
                    output.append({"Mes":str(period),"Ticker":ticker,"Tipo":SPECIAL_TYPES[ticker],
                        "Valor USD":float(val),"Estado":"OBSERVADO","Fecha":str(sample.date())})
                    continue
            fraction=(sample-start).total_seconds()/(end-start).total_seconds()
            val=float(cost)+(float(final)-float(cost))*fraction
            output.append({"Mes":str(period),"Ticker":ticker,"Tipo":SPECIAL_TYPES[ticker],
                "Valor USD":val,"Estado":"PROYECTADO LINEAL","Fecha":str(sample.date())})
    return pd.DataFrame(output,columns=["Mes","Ticker","Tipo","Valor USD","Estado","Fecha"])
