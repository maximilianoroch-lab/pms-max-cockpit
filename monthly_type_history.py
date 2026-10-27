"""Monthly USD valuations by the five requested asset types.
Only observed ticker-date snapshots; never fill missing months or missing holdings.
"""
import pandas as pd

TYPES=("Cripto","ETF","Cedear","Bono AR","Acción AR")

def monthly_type_values(history, expected_tickers=None):
    required={"Fecha","Ticker","Tipo","Valor USD"}
    if history is None or history.empty or not required.issubset(history.columns):
        return pd.DataFrame(columns=["Mes"]+list(TYPES)+["Cobertura","Estado"])
    df=history.copy()
    dates=pd.to_numeric(df["Fecha"],errors="coerce")
    df["Fecha"]=pd.to_datetime(dates,unit="D",origin="1899-12-30",errors="coerce").fillna(
        pd.to_datetime(df["Fecha"].where(dates.isna()),format="%Y-%m-%d",errors="coerce").fillna(
            pd.to_datetime(df["Fecha"].where(dates.isna()),dayfirst=True,format="mixed",errors="coerce")))
    def value(x):
        if pd.isna(x):return float("nan")
        s=str(x).strip().replace("$","").replace("US","").replace(" ","")
        if "," in s and "." in s:
            s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
        elif "," in s:s=s.replace(",",".")
        return pd.to_numeric(s,errors="coerce")
    df["Valor"]=df["Valor USD"].map(value)
    df["Ticker"]=df["Ticker"].astype(str).str.strip().str.upper()
    df=df.loc[df["Tipo"].isin(TYPES)&df["Fecha"].notna()&df["Ticker"].ne("")].copy()
    df["Mes"]=df["Fecha"].dt.to_period("M").astype(str)
    result=[]
    expected={str(t).strip().upper() for t in (expected_tickers or []) if str(t).strip()}
    for mes,part in df.groupby("Mes",sort=True):
        last_date=part["Fecha"].max()
        latest=part.loc[part["Fecha"].eq(last_date)].drop_duplicates("Ticker",keep="last")
        good=latest.loc[latest["Valor"].notna()&latest["Valor"].ge(0)]
        actual=set(good["Ticker"])
        # Never use an incomplete same-date snapshot to claim portfolio coverage.
        complete=len(good)==len(latest) and len(actual)>0 and (not expected or expected.issubset(actual))
        row={"Mes":mes,"Cobertura":len(actual),"Estado":"OBSERVADO" if complete else "INCOMPLETO"}
        for tipo in TYPES:
            row[tipo]=float(good.loc[good["Tipo"].eq(tipo),"Valor"].sum())/1000 if complete else float("nan")
        result.append(row)
    return pd.DataFrame(result,columns=["Mes"]+list(TYPES)+["Cobertura","Estado"])
