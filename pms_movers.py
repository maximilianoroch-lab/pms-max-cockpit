"""Top 10 de variaciones de cotizaciones en pesos. Nunca altera valores patrimoniales USD."""
from io import StringIO
import pandas as pd
import requests
import streamlit as st

def _number(value):
    if pd.isna(value):
        return None
    raw = str(value).strip().replace("$", "").replace(" ", "")
    if not raw:
        return None
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".") if raw.rfind(",") > raw.rfind(".") else raw.replace(",", "")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        val = float(raw)
        return val if pd.notna(val) else None
    except ValueError:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def _history(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
    response = requests.get(url, params={"tqx":"out:csv","sheet":"historial_precios","range":"A1:J5000"}, timeout=20)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text), dtype=str).fillna("")

def rank_movers(sheet_id, active_tickers):
    """Return latest synchronized ARS daily movers with last prior-month close."""
    frame = _history(sheet_id)
    required = {"Fecha","Ticker","Precio","Moneda","Precio USD"}
    if not required.issubset(frame.columns):
        raise ValueError("Historial de precios sin columnas de cotización requeridas")
    selected = {str(x).strip().upper() for x in active_tickers if str(x).strip()}
    frame["Ticker"] = frame["Ticker"].astype(str).str.strip().str.upper()
    frame = frame.loc[frame["Ticker"].isin(selected)].copy()
    frame["Fecha"] = pd.to_datetime(frame["Fecha"], dayfirst=True, format="mixed", errors="coerce")
    frame = frame.dropna(subset=["Fecha"])
    frame["Fecha"] = frame["Fecha"].dt.normalize()
    frame["Moneda"] = frame["Moneda"].astype(str).str.upper().str.strip()
    frame["raw_price"] = frame["Precio"].map(_number)
    frame["usd_price"] = frame["Precio USD"].map(_number)
    frame = frame.loc[frame["raw_price"].gt(0)].copy()
    # The contemporaneous conversion ratio is inferred from the feed (ARS / USD).
    # Never treat position value, quantity, variation in USD, or a different day's FX as unit price.
    refs = frame.loc[(frame["Moneda"]=="ARS") & frame["usd_price"].gt(0)].copy()
    refs["fx"] = refs["raw_price"] / refs["usd_price"]
    refs = refs.loc[refs["fx"].between(100, 10000)]
    counts = refs.groupby("Fecha")["fx"].count()
    medians = refs.groupby("Fecha")["fx"].median()
    fx = medians.loc[counts.ge(3)]
    frame["ARS"] = frame["raw_price"].where(frame["Moneda"]=="ARS")
    crypto = frame["Ticker"].isin(["BTC","ETH","ADA","SOL","XRP"])
    mask = crypto & frame["Moneda"].eq("USD")
    frame.loc[mask, "ARS"] = frame.loc[mask, "raw_price"] * frame.loc[mask, "Fecha"].map(fx)
    frame = frame.loc[frame["ARS"].gt(0)].copy()
    # A single daily observation per instrument. Missing trading days are skipped naturally.
    frame = frame.sort_values("Fecha").drop_duplicates(["Ticker","Fecha"], keep="last")
    ranked = []
    for ticker, group in frame.groupby("Ticker"):
        group = group.sort_values("Fecha")
        if len(group) < 2:
            continue
        last, previous = group.iloc[-1], group.iloc[-2]
        month_start = last["Fecha"].replace(day=1)
        prior_month = month_start - pd.Timedelta(days=1)
        monthly_base = group.loc[group["Fecha"].dt.to_period("M").eq(prior_month.to_period("M"))]
        month_close = monthly_base.iloc[-1] if not monthly_base.empty else None
        daily = (last["ARS"] / previous["ARS"] - 1) * 100
        monthly = (last["ARS"] / month_close["ARS"] - 1) * 100 if month_close is not None else None
        ranked.append({"Activo":ticker,"Cotización ARS":float(last["ARS"]),
                       "Diaria %":float(daily),"Mes %":float(monthly) if monthly is not None else None,
                       "Fecha":last["Fecha"],"Previo":previous["Fecha"]})
    if not ranked:
        return pd.DataFrame(), None
    result = pd.DataFrame(ranked)
    common_close = result["Fecha"].max()
    return result.loc[result["Fecha"].eq(common_close)].copy(), common_close

def show_top10(st, sheet_id, active_tickers, key="movers"):
    st.subheader("Mayores variaciones de cotización · ARS")
    st.caption("Precios unitarios en pesos; tenencias, agrupaciones y patrimonio se mantienen en USD. "
               "El ranking depende exclusivamente de la variación entre los dos últimos cierres válidos del activo.")
    try:
        movements, close = rank_movers(sheet_id, active_tickers)
    except (requests.RequestException, ValueError, KeyError) as exc:
        st.info("No se pudo verificar el historial de cotizaciones; no se muestran porcentajes estimados.")
        st.caption(str(exc)[:180])
        return
    if movements.empty:
        st.info("No hay dos cierres unitarios en ARS verificables para elaborar el ranking.")
        return
    st.caption(f"Cierre común: {close.strftime('%d/%m/%Y')} · la fuente puede estar retrasada. "
               "Cripto USD: conversión a ARS usando tipo de cambio implícito del historial fechado. "
               "Futuros sin cotización de contrato comparable no se incluyen.")
    cols = st.columns(2)
    for slot, title, direction, ascending in [(cols[0],"Top 10 subas",1,False),
                                               (cols[1],"Top 10 bajas",-1,True)]:
        with slot:
            st.markdown("**"+title+"**")
            rows = movements.loc[movements["Diaria %"].gt(0) if direction>0 else movements["Diaria %"].lt(0)]
            rows = rows.sort_values("Diaria %", ascending=ascending).head(10)
            if rows.empty:
                st.caption("Sin activos con variación de este signo.")
                continue
            display = rows[["Activo","Cotización ARS","Diaria %","Mes %"]].copy()
            styler = display.style.format({"Cotización ARS":lambda v:f"$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                          "Diaria %":lambda v:f"{v:+.2f}%",
                                          "Mes %":lambda v: "Sin datos" if pd.isna(v) else f"{v:+.2f}%"})
            def paint(value):
                if pd.isna(value):
                    return "color:#93a7bd"
                return "color:#54d49a" if value>0 else "color:#ff7a7a" if value<0 else "color:#93a7bd"
            styler = styler.map(paint, subset=["Diaria %","Mes %"])
            st.dataframe(styler, hide_index=True, width="stretch")
