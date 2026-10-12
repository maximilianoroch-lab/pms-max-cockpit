
from io import StringIO
import requests, pandas as pd

FEEDS={
"looker_feed_v2":"A1:T2000","app_feed_v2":"A1:T67","app_home":"A69:F77","app_banner":"A80:D89",
"dashboard_diversificacion_v2":"A1:E20","dashboard_exposicion_v2":"A1:J30","dashboard_riesgo_v2":"A1:E30",
"dashboard_evolucion_v2":"A1:F30","dashboard_custodia_v2":"A1:E30","dashboard_tipo_v2":"A1:F20",
"app_custodia_detalle_v2":"A1:L500","app_custodia_resumen_v2":"A1:J30"}

def _url(sid,sheet,rg): return f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={sheet}&range={rg}"

def parse_num(v):
    s=str(v).replace("$","").replace("%","").strip()
    if s in ("","nan","None"): return 0.0
    if "," in s and "." in s:
        s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
    elif "," in s:s=s.replace(",",".")
    try:return float(s)
    except:return 0.0

def add_num(df,col,new=None,pct=False):
    if col in df:
        name=new or col+"_num"
        df[name]=df[col].map(parse_num)
        if pct: df[name]=df[name]/100
    return df

def normalize(name,df):
    df=df.copy()
    df.columns=[str(c).strip() for c in df.columns]
    for c in ["Valor USD","Valor total USD","Impacto USD","Cotización local","Valor ref USD","Cantidad"]:
        add_num(df,c)
    for c in ["Peso","Peso cartera","Peso custodio","Variación %","Impacto cartera %"]:
        add_num(df,c,pct=True)

    # Aliases estables usados por la UI. Evitan depender del nombre literal
    # generado a partir de columnas que contienen espacios o símbolos.
    if "Variación %_num" in df.columns:
        df["Variación_num"]=df["Variación %_num"]
    if "Impacto cartera %_num" in df.columns:
        df["Impacto cartera_num"]=df["Impacto cartera %_num"]
    if "Impacto USD" in df.columns and "Impacto USD_num" not in df.columns:
        add_num(df,"Impacto USD","Impacto USD_num")
    if name=="dashboard_exposicion_v2":
        if "Valor USD.1" in df:add_num(df,"Valor USD.1","Sector Valor USD_num")
        else:df["Sector Valor USD_num"]=0
        if "Peso.1" in df:add_num(df,"Peso.1","Sector Peso_num",True)
        else:df["Sector Peso_num"]=0
    if name=="app_custodia_resumen_v2":
        add_num(df,"Cantidad cuentas","Cantidad cuentas_num")
        if "Peso cartera_num" not in df:add_num(df,"Peso cartera","Peso cartera_num",True)
    return df

def load_all_data(sid):
    out={}
    for name,rg in FEEDS.items():
        sheet="app_feed_v2" if name in ("app_home","app_banner") else name
        r=requests.get(_url(sid,sheet,rg),timeout=15);r.raise_for_status()
        out[name]=normalize(name,pd.read_csv(StringIO(r.text)))
    return out

def _firstcol_map(df):
    out={}
    if df is None or df.empty:return out
    k=df.columns[0]
    for _,r in df.iterrows():
        if pd.notna(r[k]):out[str(r[k])]=r
    return out

def portfolio_summary(data):
    hm=_firstcol_map(data["app_home"]); bm=_firstcol_map(data["app_banner"])
    def val(name,p=False):
        r=hm.get(name)
        return parse_num(r.get("Valor",0))/100 if p and r is not None else parse_num(r.get("Valor",0)) if r is not None else 0
    def ch(name):
        r=hm.get(name); return parse_num(r.get("Variación",0))/100 if r is not None else 0
    app=data["app_feed_v2"]; last=""
    if not app.empty and "Fecha dato" in app:
        x=app["Fecha dato"].dropna().astype(str)
        if not x.empty:last=x.iloc[0]
    upd="";r=bm.get("Actualización de precios")
    if r is not None:upd=str(r.get("Valor",""))
    return {"non_crypto":val("Patrimonio sin Crypto"),"crypto":val("Crypto USD"),"crypto_pct":val("Crypto %",True),"total":val("Patrimonio total"),
    "argentina_pct":val("Argentina %",True),"top5_pct":val("Top 5 %",True),"positions_count":val("Cantidad posiciones"),
    "non_crypto_change":ch("Patrimonio sin Crypto"),"crypto_change":ch("Crypto %"),"total_change":ch("Patrimonio total"),
    "argentina_change":ch("Argentina %"),"top5_change":ch("Top 5 %"),"price_update":upd,"last_market":last}

def enrich_positions(data): return data.get("looker_feed_v2",pd.DataFrame()).copy()

def quote_text(r):
    ticker=str(r.get("Ticker","")); typ=str(r.get("Tipo","")); status=str(r.get("Estado dato","")).upper();current=status=="ACTUALIZADO"
    qty=float(r.get("Cantidad_num",0) or 0);value=float(r.get("Valor USD_num",0) or 0);local=float(r.get("Cotización local_num",0) or 0)
    cur=str(r.get("Moneda cotización",""));ref=float(r.get("Valor ref USD_num",0) or 0)
    usdq=lambda x:"< US$ 1" if 0<x<1 else f"US$ {x:,.0f}".replace(",",".")
    arsq=lambda x:f"$ {x:,.0f}".replace(",",".")
    if typ=="Cripto" and qty>0:return ("" if current else "Últ. ")+usdq(value/qty)
    if ticker=="FUT":
        q=(ref or value)/qty if qty else (ref or value);return "Últ. "+usdq(q)
    if cur=="ARS" and local>0:return ("" if current else "Últ. ")+arsq(local)
    if ticker=="CASH":return "Últ. "+usdq(ref or value)
    return "—"
