"""Pure portfolio-position comparison shared by Bersoch and DEMO.

No network, prices, company fundamentals or portfolio-specific source assumptions.
"""
import pandas as pd
import math

def compare_portfolio_positions(positions, left, right, total=None):
    a,b=str(left or "").upper().strip(),str(right or "").upper().strip()
    if not a or not b or a==b:
        raise ValueError("Seleccioná dos instrumentos distintos")
    required={"Ticker","Valor USD_num"}
    if not required.issubset(positions.columns):
        raise ValueError("Faltan columnas de cartera para comparar")
    frame=positions.copy()
    frame["Ticker"]=frame["Ticker"].astype(str).str.upper().str.strip()
    frame["Valor USD_num"]=pd.to_numeric(frame["Valor USD_num"],errors="raise")
    if not frame["Valor USD_num"].map(math.isfinite).all() or (frame["Valor USD_num"]<0).any():
        raise ValueError("Valor de posición inválido")
    values=frame.groupby("Ticker")["Valor USD_num"].sum()
    if not values.map(math.isfinite).all():
        raise ValueError("El total agregado contiene valores inválidos")
    if a not in values or b not in values:
        raise ValueError("El instrumento no pertenece a la cartera")
    if total is None:total=float(values.sum())
    if not math.isfinite(float(total)) or float(total)<=0:
        raise ValueError("El patrimonio debe ser positivo")
    total=float(total)
    if values.sum()>total+max(0.02,total*1e-6):
        raise ValueError("El detalle supera el patrimonio suministrado")
    result=[]
    for ticker in (a,b):
        sub=frame.loc[frame["Ticker"]==ticker]
        val=float(values[ticker])
        qty_col="Cantidad" if "Cantidad" in sub.columns else "Cantidad_num" if "Cantidad_num" in sub.columns else None
        quantity=None
        if qty_col:
            qty=pd.to_numeric(sub[qty_col],errors="coerce")
            if qty.notna().all() and qty.map(math.isfinite).all() and (qty>=0).all():
                quantity=float(qty.sum())
        entry={"Ticker":ticker,"Valor USD":val,"Peso cartera":val/total,
               "Tipo":str(sub["Tipo"].dropna().iloc[0]) if "Tipo" in sub and sub["Tipo"].notna().any() else "—"}
        if quantity is not None and quantity>0:
            entry["Cantidad"]=quantity
            entry["Precio medio USD"]=val/quantity
        result.append(entry)
    return pd.DataFrame(result)
