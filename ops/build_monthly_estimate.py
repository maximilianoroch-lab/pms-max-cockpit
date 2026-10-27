"""Build a 34-month APPROXIMATE Bersoch allocation history.
This is a decision-support estimate, NOT a verified performance series.
Reconcile quantities from the operation log; observed monthly positions override estimates.
"""
import csv,datetime as dt,io,pathlib,collections
import pandas as pd
import requests
from ops.market_coverage_audit import sheet_rows
from ops.data912_monthly_audit import fetch_ticker
from ops.binance_monthly_audit import fetch_symbol,SUPPORTED
TYPES={"Cripto":"Cripto","ETF":"ETF","Fondo":"ETF","Cedear":"CEDEAR",
       "Bono AR":"Bonos","Acción AR":"Acciones"}
MONTHS=pd.period_range("2024-01","2026-10",freq="M")
SPECIAL={"FUT":"Cripto","GALILEO":"ETF","SCHROD":"ETF"}
def n(x):
    try:
        s=str(x).replace(" ","").replace("$","")
        if s.lower() in ("","nan","none"):return float("nan")
        if "," in s and "." in s:s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
        else:s=s.replace(",",".")
        return float(s)
    except (ValueError,TypeError):return float("nan")
def date(v):
    value=n(v)
    if pd.notna(value) and 35000<value<60000:
        return (pd.Timestamp("1899-12-30")+pd.Timedelta(days=value)).normalize()
    s=str(v).strip()
    iso=pd.to_datetime(s,format="%Y-%m-%d",errors="coerce")
    return iso if pd.notna(iso) else pd.to_datetime(s,dayfirst=True,errors="coerce")
def main():
    with requests.Session() as session:
        ops=pd.DataFrame(sheet_rows("operaciones_normalizadas",session))
        feed=pd.DataFrame(sheet_rows("app_feed_v2",session))
        forex=pd.DataFrame(sheet_rows("tc_diario",session))
        observed=pd.DataFrame(sheet_rows("historial_precios",session))
        custody=pd.DataFrame(sheet_rows("tenencias_custodio",session))
        ops["day"]=ops["Fecha"].map(date)
        ops["quantity"]=ops["Cantidad"].map(n)
        ops["flow"]=ops["Flujo USD"].map(n)
        feed["value"]=feed["Valor USD"].map(n)
        observed["day"]=observed["Fecha"].map(date)
        observed["value"]=observed["Valor USD"].map(n)
        observed["quantity"]=observed["Cantidad"].map(n)
        fx=forex.copy();fx["day"]=fx["Fecha"].map(date)
        fx["CCL"]=fx["CCL"].map(n);fx["MEP"]=fx["MEP"].map(n)
        fx=fx.dropna(subset=["day"]).sort_values("day").drop_duplicates("day",keep="last")
        def fxat(d,kind):
            if fx.empty:return float("nan")
            x=fx.loc[fx["day"]<=d,kind].dropna()
            if x.empty:x=fx.loc[fx["day"]>=d,kind].dropna()
            return float(x.iloc[-1]) if len(x) else float("nan")
        events=ops.loc[ops["Evento"].isin(("Compra","Venta","Dividendo en acciones","Split"))].copy()
        quantities=collections.defaultdict(float)
        by_month=collections.defaultdict(dict)
        for m in MONTHS:
            for _,r in events.loc[events["day"].dt.to_period("M")==m].iterrows():
                ticker=r["Ticker"].strip().upper()
                q=r["quantity"]
                if ticker and pd.notna(q):quantities[ticker]+=q
            by_month[str(m)]=dict(quantities)
        ticker_kind=dict(zip(ops["Ticker"].str.upper(),ops["Tipo"]))
        ticker_kind.update(dict(zip(feed["Ticker"].str.upper(),feed["Tipo"])))
        all_tickers={t for q in by_month.values() for t,v in q.items() if v>1e-9}
        prices={}
        for ticker in sorted(all_tickers):
            kind=ticker_kind.get(ticker,"")
            if kind not in ("Acción AR","Cedear","Bono AR"):continue
            try:
                items,status=fetch_ticker(session,ticker,kind,timeout=24)
                if status=="OK":prices[ticker]={r["mes"]:float(r["cierre_ars"]) for r in items}
            except Exception:pass
        crypto={}
        for ticker in SUPPORTED:
            try:crypto[ticker]={r["Mes"]:float(r["Precio USDT"]) for r in fetch_symbol(ticker,session=session)}
            except Exception:pass
        # Oct observed unit prices provide a stable instrument-specific quotation normalization.
        anchor={}
        for ticker,group in observed.groupby("Ticker"):
            group=group.dropna(subset=["day","quantity","value"]).sort_values("day")
            group=group.loc[group["quantity"].gt(0)]
            if not group.empty:
                row=group.iloc[-1]
                anchor[str(ticker).upper()]=(row["day"],float(row["value"]/row["quantity"]))
        avgcost={}
        for ticker,group in ops.loc[ops["Evento"].eq("Compra")].groupby("Ticker"):
            qty=group["quantity"].sum()
            cost=-group["flow"].sum()
            if pd.notna(qty) and qty>0 and pd.notna(cost) and cost>=0:
                avgcost[ticker.upper()]=float(cost/qty)
        # interpolate FUT, GALILEO, SCHROD: USD cost to latest manual USD valuation.
        special={}
        for t in SPECIAL:
            buy=ops.loc[ops["Ticker"].str.upper().eq(t)&ops["Evento"].eq("Compra")].sort_values("day")
            live=feed.loc[feed["Ticker"].str.upper().eq(t)]
            if len(buy)==1 and len(live)==1:
                first=buy.iloc[0];start=first["day"]
                cost=-first["flow"];final=live.iloc[0]["value"]
                if pd.notna(start) and pd.notna(cost) and pd.notna(final):
                    special[t]=(start,float(cost),pd.Timestamp("2026-10-27"),float(final))
        results=[];audit=[]
        for m in MONTHS:
            month=str(m);stop=min(m.end_time.normalize(),pd.Timestamp("2026-10-27"))
            bucket={t:0.0 for t in ("Cripto","ETF","CEDEAR","Bonos","Acciones")}
            estimated=0;external=0;priced=0;used=0
            for ticker,qty in by_month[month].items():
                if qty<=1e-9:continue
                kind=ticker_kind.get(ticker,"")
                category=SPECIAL.get(ticker,TYPES.get(kind))
                if category is None:continue
                used+=1;value=None;status="ESTIMADO"
                if ticker in special:
                    start,cost,end,final=special[ticker]
                    if stop>=start:
                        ratio=min(1.,max(0.,(stop-start).days/max(1,(end-start).days)))
                        value=cost+(final-cost)*ratio
                elif ticker in crypto and month in crypto[ticker]:
                    value=qty*crypto[ticker][month];status="PRECIO BINANCE";external+=1
                elif ticker in prices and month in prices[ticker]:
                    raw=prices[ticker][month]
                    month_fx=fxat(stop,"MEP" if category=="Bonos" else "CCL")
                    day,p_anchor=anchor.get(ticker,(None,None))
                    # Rather than guessing quoted bond/CEDEAR units, anchor relative prices.
                    anchor_month=str(day.to_period("M")) if day is not None else ""
                    raw_anchor=prices[ticker].get(anchor_month)
                    if raw_anchor and p_anchor and pd.notna(month_fx) and month_fx>0:
                        fx_anchor=fxat(day,"MEP" if category=="Bonos" else "CCL")
                        unit=p_anchor*(raw/raw_anchor)*(fx_anchor/month_fx)
                        value=qty*unit;status="PRECIO DATA912 ANCLADO";external+=1
                    elif pd.notna(month_fx) and month_fx>0 and raw>0:
                        # Fallback to position-specific dollar cost; never assume bond units.
                        base=avgcost.get(ticker)
                        if base is not None:
                            value=qty*base;status="COSTO USD APROXIMADO"
                if value is None:
                    last=anchor.get(ticker)
                    unit=last[1] if last else avgcost.get(ticker)
                    if unit is None or not pd.notna(unit):continue
                    value=qty*unit
                else:priced+=1
                if status=="ESTIMADO" or status=="COSTO USD APROXIMADO":estimated+=1
                if pd.notna(value) and value>=0:bucket[category]+=value
            # Current observed monthly type totals are authoritative when available.
            observations=observed.loc[observed["day"].dt.to_period("M")==m]
            state="ESTIMADO"
            if not observations.empty:
                lastday=observations["day"].max()
                snap=observations.loc[observations["day"].eq(lastday)]
                if len(snap)>=50:
                    obs_bucket={k:0. for k in bucket}
                    for _,r in snap.iterrows():
                        cat=SPECIAL.get(str(r["Ticker"]).upper(),TYPES.get(r["Tipo"]))
                        if cat and pd.notna(r["value"]):obs_bucket[cat]+=r["value"]
                    bucket=obs_bucket;state="OBSERVADO OCT 2026"
            results.append({"Mes":month,**{k:round(v/1000,3) for k,v in bucket.items()},
                "Total cinco tipos (miles USD)":round(sum(bucket.values())/1000,3),
                "Estado":state,"Instrumentos con tenencia":used,
                "Con precio externo":external,"Estimados":estimated})
        path=pathlib.Path("market_audit");path.mkdir(exist_ok=True)
        out=path/"bersoch_2024_2026_monthly_estimate.csv"
        with out.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
        import json
        print("MONTHLY_SERIES_JSON="+json.dumps(results,ensure_ascii=False,allow_nan=False))
        print("MESES_GENERADOS",len(results))
        print("PRIMER_MES",results[0])
        print("ULTIMO_MES",results[-1])
        print("ESTIMACIONES_TICKERS",sum(x["Estimados"] for x in results))
        print("ADVERTENCIA: No conciliado a cierre anual ni ajustado por splits/compras previas no registradas; no es rentabilidad.")
if __name__=="__main__":main()
