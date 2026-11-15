"""Controles descriptivos de históricos PMS; no modifica cotizaciones ni snapshots."""
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

TZ=ZoneInfo("America/Argentina/Buenos_Aires")

def history_status(dates, today=None):
    """Días hábiles transcurridos desde el último cierre observado; feriados no modelados."""
    today=pd.Timestamp(today or datetime.now(TZ).date()).normalize()
    valid=pd.to_datetime(pd.Series(list(dates)),dayfirst=True,format="mixed",errors="coerce").dropna().dt.normalize()
    if valid.empty:
        return {"latest":None,"business_days_missing":None,"last_observations":0}
    latest=valid.max()
    days=int(len(pd.bdate_range(latest+pd.Timedelta(days=1),today-pd.Timedelta(days=1)))) if today>latest else 0
    return {"latest":latest,"business_days_missing":days,"last_observations":int(valid.nunique())}

def parse_ars_price(value):
    """Parse common ARS formats, rejecting ambiguous and invalid values.

    Google CSV may expose English 23100.50, locale 23.100,50 or
    23.100 (thousands grouped). A plain dot with 1-2 decimals is decimal.
    """
    import math
    if value is None or pd.isna(value):
        return None
    raw=str(value).strip().replace("$","").replace("ARS","").replace(" ","").replace("\\u00a0","")
    if not raw:
        return None
    if "," in raw and "." in raw:
        if raw.rfind(",")>raw.rfind("."):
            raw=raw.replace(".","").replace(",",".")
        else:
            raw=raw.replace(",","")
    elif "," in raw:
        parts=raw.split(",")
        raw=raw.replace(",","") if len(parts)==2 and len(parts[1])==3 and len(parts[0])<=3 else raw.replace(",",".")
    elif "." in raw:
        parts=raw.split(".")
        if len(parts)>1 and all(len(p)==3 for p in parts[1:]) and len(parts[0])<=3:
            raw=raw.replace(".","")
    try:
        result=float(raw)
        return result if math.isfinite(result) and result>0 else None
    except ValueError:
        return None

def suspicious_constant_quote(history, ticker, comparison_price, threshold=0.40):
    """Devuelve advertencia de fuerte discrepancia, nunca precio corregido."""
    if history is None or history.empty or comparison_price is None or comparison_price<=0:
        return None
    required={"Ticker","Fecha","Precio","Moneda"}
    if not required.issubset(history.columns):return None
    rows=history.loc[history["Ticker"].astype(str).str.upper().eq(str(ticker).upper())].copy()
    if rows.empty:return None
    rows["parsed"]=rows["Precio"].map(parse_ars_price)
    rows=rows.loc[rows["Moneda"].astype(str).str.upper().eq("ARS")&rows["parsed"].gt(0)]
    if len(rows)<3:return None
    unique=rows["parsed"].round(4).nunique()
    last=float(rows["parsed"].iloc[-1])
    discrepancy=abs(comparison_price/last-1)
    if unique==1 and discrepancy>=threshold:
        return {"ticker":ticker,"historic_price_ars":last,"reference_price_ars":float(comparison_price),
                "difference_pct":float(discrepancy*100),"observations":int(len(rows))}
    return None
