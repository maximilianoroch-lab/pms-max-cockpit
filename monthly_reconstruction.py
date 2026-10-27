"""Conservative monthly position reconstruction; never fabricates closing prices."""
import pandas as pd

QUANTITY_EVENTS={"Compra","Venta","Dividendo en acciones","Split"}
UNRESOLVED_EVENTS={"Put","Call","Amortización"}

def monthly_quantities(operations):
    required={"Fecha","Evento","Ticker","Cantidad","Tipo"}
    if operations is None or not required.issubset(operations.columns):
        raise ValueError("Faltan columnas de operaciones")
    frame=operations.copy()
    number=pd.to_numeric(frame["Fecha"],errors="coerce")
    frame["Fecha"]=pd.to_datetime(number,unit="D",origin="1899-12-30",errors="coerce").fillna(
        pd.to_datetime(frame["Fecha"].where(number.isna()),format="%Y-%m-%d",errors="coerce").fillna(pd.to_datetime(frame["Fecha"].where(number.isna()),dayfirst=True,format="mixed",errors="coerce"))
    )
    frame["Cantidad"]=pd.to_numeric(frame["Cantidad"],errors="coerce")
    frame=frame.dropna(subset=["Fecha"])
    frame["Ticker"]=frame["Ticker"].fillna("").astype(str).str.strip().str.upper()
    frame["Tipo"]=frame["Tipo"].fillna("Sin clasificar").astype(str)
    frame["Evento"]=frame["Evento"].fillna("").astype(str).str.strip()
    valid=frame.loc[frame["Evento"].isin(QUANTITY_EVENTS)&frame["Ticker"].ne("")&frame["Cantidad"].notna()].copy()
    if valid.empty:
        return pd.DataFrame(columns=["Mes","Ticker","Tipo","Cantidad"]),pd.DataFrame(columns=["Mes","Eventos sin conciliación"])
    valid["Mes"]=valid["Fecha"].dt.to_period("M")
    valid["Cuenta"]=valid["Cuenta PMS"].fillna("").astype(str) if "Cuenta PMS" in valid.columns else ""
    # Keep account distinction until aggregated; splits are already recorded as delta quantities in the ledger.
    monthly=valid.groupby(["Mes","Ticker","Tipo"],as_index=False)["Cantidad"].sum()
    months=pd.period_range(frame["Fecha"].min().to_period("M"),frame["Fecha"].max().to_period("M"),freq="M")
    snapshots=[]
    for key,group in monthly.groupby(["Ticker","Tipo"],sort=False):
        s=group.set_index("Mes")["Cantidad"].reindex(months,fill_value=0).cumsum()
        snapshots.extend({"Mes":str(m),"Ticker":key[0],"Tipo":key[1],"Cantidad":float(q)} for m,q in s.items() if abs(q)>1e-9)
    pending=frame.loc[frame["Evento"].isin(UNRESOLVED_EVENTS)].copy()
    pending["Mes"]=pending["Fecha"].dt.to_period("M").astype(str)
    exceptions=pending.groupby("Mes").size().rename("Eventos sin conciliación").reset_index()
    return pd.DataFrame(snapshots,columns=["Mes","Ticker","Tipo","Cantidad"]),exceptions
