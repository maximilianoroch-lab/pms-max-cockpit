
import streamlit as st
import pandas as pd
import plotly.express as px

from data import load_all_data, portfolio_summary, enrich_positions, quote_text
from advisor import ask_advisor, build_action_prompt, compare_companies_structured
from portfolio_config import PORTFOLIO

st.set_page_config(page_title=PORTFOLIO["app_name"], page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; max-width: 1700px;}
[data-testid="stSidebar"] {background: #091522;}
[data-testid="stDataFrame"] {font-size: 0.92rem;}
.metric-card {background:linear-gradient(180deg,#0d1b2b,#0a1827);border:1px solid #28455f;border-radius:14px;padding:14px 16px;min-height:112px}
.metric-label{color:#93a7bd;font-size:12px;font-weight:700;text-transform:uppercase}
.metric-value{color:#f4f7fb;font-size:24px;font-weight:900;margin-top:6px;white-space:nowrap}
.metric-sub{color:#93a7bd;font-size:11px;margin-top:6px}
.up{color:#54d49a;font-weight:800}.down{color:#ff7a7a;font-weight:800}.flat{color:#93a7bd;font-weight:800}
</style>
""", unsafe_allow_html=True)

SHEET_ID=PORTFOLIO["sheet_id"]

@st.cache_data(ttl=180, show_spinner=False)
def get_data():
    return load_all_data(SHEET_ID)

data=get_data()
summary=portfolio_summary(data)
positions=enrich_positions(data)

if "analysis_context" not in st.session_state:
    st.session_state["analysis_context"]={"dimension":"","value":""}

def apply_analysis_context(df):
    ctx=st.session_state.get("analysis_context",{"dimension":"","value":""})
    dim,val=ctx.get("dimension",""),ctx.get("value","")
    if df is None or df.empty or not val:
        return df
    colmap={"Región":"Región directa","Sector":"Sector directo","Custodio":"Custodio","Clase":"Clase","Tipo":"Tipo"}
    col=colmap.get(dim)
    if col and col in df.columns:
        return df[df[col].astype(str)==str(val)].copy()
    return df

with st.sidebar:
    st.title(PORTFOLIO["display_name"])
    st.caption("Cockpit · análisis + asesor IA")
    st.markdown("### Dashboard")
    page=st.radio(
        "Dashboard",
        ["Resumen","Diversificación","Evolución","Riesgo","Custodia","Posiciones"],
        label_visibility="collapsed",
        key="dashboard_nav"
    )
    st.markdown("### Herramientas")
    tool_page=st.radio(
        "Herramientas",
        ["—","Comparador","Simulador"],
        label_visibility="collapsed",
        key="tools_nav"
    )
    st.markdown("### IA")
    ai_open=st.button("Asesor IA",use_container_width=True)
    if ai_open:
        st.session_state["force_page"]="Asesor IA"
    if tool_page!="—":
        page=tool_page
    if st.session_state.get("force_page")=="Asesor IA":
        page="Asesor IA"
    st.divider()
    filtered=positions.copy()
    if not positions.empty:
        all_tickers=sorted(positions["Ticker"].dropna().astype(str).unique().tolist())
        active_default=st.session_state.get("active_ticker","")
        ticker_options=["—"]+all_tickers
        ticker_index=ticker_options.index(active_default) if active_default in ticker_options else 0
        selected_ticker=st.selectbox("Ticker activo",ticker_options,index=ticker_index,help="Este ticker se comparte con el Asesor IA y otras vistas.")
        st.session_state["active_ticker"]="" if selected_ticker=="—" else selected_ticker

        custodios=["Todos"]+sorted(positions["Custodio"].dropna().astype(str).unique().tolist())
        tipos=["Todos"]+sorted(positions["Tipo"].dropna().astype(str).unique().tolist())
        regiones=["Todas"]+sorted(positions["Región directa"].dropna().astype(str).unique().tolist())
        sel_cust=st.selectbox("Custodio",custodios)
        sel_tipo=st.selectbox("Tipo",tipos)
        sel_region=st.selectbox("Región",regiones)
        if sel_cust!="Todos": filtered=filtered[filtered["Custodio"]==sel_cust]
        if sel_tipo!="Todos": filtered=filtered[filtered["Tipo"]==sel_tipo]
        if sel_region!="Todas": filtered=filtered[filtered["Región directa"]==sel_region]
        filtered=apply_analysis_context(filtered)
    else:
        st.session_state["active_ticker"]=""
    ctx=st.session_state.get("analysis_context",{"dimension":"","value":""})
    if ctx.get("value"):
        st.info(f'Contexto: {ctx.get("dimension")} · {ctx.get("value")}')
        if st.button("Limpiar contexto",use_container_width=True):
            st.session_state["analysis_context"]={"dimension":"","value":""}
            st.rerun()

    if st.button("Actualizar datos",use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.caption(f'Fuente: {PORTFOLIO["display_name"]} · {summary.get("last_market","—")}')
    try: has_key=bool(st.secrets.get("OPENAI_API_KEY",""))
    except Exception: has_key=False
    st.caption("Asesor IA: "+("configurado" if has_key else "pendiente de API key"))

def fmt_usd(x):
    try:
        n=float(x)
        s=f"{n:,.0f}".replace(",","X").replace(".",",").replace("X",".")
        return f"US$ {s}"
    except:
        return "—"

def fmt_num(x,decimals=0):
    try:
        n=float(x)
        s=f"{n:,.{decimals}f}".replace(",","X").replace(".",",").replace("X",".")
        return s
    except:
        return "—"

def fmt_pct(x,decimals=1):
    try:
        return f"{float(x)*100:.{decimals}f}%".replace(".",",")
    except:
        return "—"
def pct_points(series):
    try:
        return pd.to_numeric(series,errors="coerce")*100
    except:
        return series

def local_num(v):
    s=str(v).replace("$","").replace("%","").strip()
    if s in ("","nan","None"): return 0.0
    if "," in s and "." in s:
        s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
    elif "," in s:
        s=s.replace(",",".")
    try: return float(s)
    except: return 0.0

def compact_status(v):
    s=str(v or "")
    repl={
        "TC MEP DESACTUALIZADO":"Último MEP",
        "TC CCL DESACTUALIZADO":"Último CCL",
        "MANUAL":"Manual",
        "ACTUALIZADO":"Actualizado",
    }
    return repl.get(s,s)

def compact_name(v,max_len=26):
    s=str(v or "")
    return s if len(s)<=max_len else s[:max_len-1]+"…"
def change_html(v):
    try:x=float(v)
    except:x=0
    if x>0:return f'<span class="up">▲ +{x*100:.1f}%</span>'
    if x<0:return f'<span class="down">▼ {x*100:.1f}%</span>'
    return '<span class="flat">→ 0,0%</span>'
def metric_card(label,value,sub="",change=None):
    delta=f"<div>{change_html(change)}</div>" if change is not None else ""
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div>{delta}</div>',unsafe_allow_html=True)

def split_wealth_card(crypto,crypto_pct,non_crypto):
    html = (
        '<div class="metric-card">'
        '<div class="metric-label">DESGLOSE</div>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:10px">'
        '<div>'
        '<div class="metric-sub">Crypto</div>'
        f'<div class="metric-value" style="font-size:20px">{fmt_usd(crypto)}</div>'
        f'<div class="metric-sub">{fmt_pct(crypto_pct)}</div>'
        '</div>'
        '<div style="border-left:1px solid #28455f;padding-left:14px">'
        '<div class="metric-sub">Sin Crypto</div>'
        f'<div class="metric-value" style="font-size:20px">{fmt_usd(non_crypto)}</div>'
        '<div class="metric-sub">Capital principal</div>'
        '</div></div></div>'
    )
    st.markdown(html,unsafe_allow_html=True)

def active_ticker_snapshot(ticker):
    if not ticker:
        return None
    app_df=data.get("app_feed_v2",pd.DataFrame())
    pos_df=data.get("looker_feed_v2",pd.DataFrame())
    a=app_df[app_df["Ticker"].astype(str)==ticker] if not app_df.empty else pd.DataFrame()
    p=pos_df[pos_df["Ticker"].astype(str)==ticker] if not pos_df.empty else pd.DataFrame()
    if a.empty and p.empty:
        return None
    row=a.iloc[0] if not a.empty else p.iloc[0]
    return {
        "Ticker":ticker,
        "Nombre":row.get("Nombre",""),
        "Valor USD": float(a["Valor USD_num"].sum()) if not a.empty and "Valor USD_num" in a else float(p["Valor USD_num"].sum()) if not p.empty else 0,
        "Peso": float(a["Peso_num"].iloc[0]) if not a.empty and "Peso_num" in a else float(p["Peso cartera_num"].sum()) if not p.empty else 0,
        "Variación": float(a["Variación_num"].iloc[0]) if not a.empty and "Variación_num" in a else 0,
        "Clase": row.get("Clase",""),
        "Tipo": row.get("Tipo",""),
        "Región": row.get("Región",row.get("Región directa","")),
        "Sector": row.get("Sector",row.get("Sector directo","")),
        "Custodios": ", ".join(sorted(p["Custodio"].dropna().astype(str).unique())) if not p.empty else "",
        "Cuentas": ", ".join(sorted(p["Cuenta"].dropna().astype(str).unique())) if not p.empty else "",
    }


def set_context(dim,value):
    st.session_state["analysis_context"]={"dimension":dim,"value":str(value)}
    st.rerun()

def render_global_context_banner():
    ctx=st.session_state.get("analysis_context",{"dimension":"","value":""})
    ticker=st.session_state.get("active_ticker","")
    parts=[]
    if ticker: parts.append(f"Ticker: {ticker}")
    if ctx.get("value"): parts.append(f'{ctx.get("dimension")}: {ctx.get("value")}')
    if parts: st.info("Contexto activo · "+" · ".join(parts))

def top_positions_table(limit=12):
    app_df=data.get("app_feed_v2",pd.DataFrame()).copy()
    if app_df.empty: return
    top=app_df[app_df["Ticker"].notna()].sort_values("Valor USD_num",ascending=False).head(limit)
    top_show=top[["Ticker","Nombre","Valor USD_num","Peso_num","Variación_num","Estado dato"]].copy()
    top_show["Nombre"]=top_show["Nombre"].map(compact_name)
    top_show["Estado dato"]=top_show["Estado dato"].map(compact_status)
    top_show["Peso_num"]=pct_points(top_show["Peso_num"])
    top_show["Variación_num"]=pct_points(top_show["Variación_num"])
    ev=st.dataframe(
        top_show,
        hide_index=True,use_container_width=True,on_select="rerun",selection_mode="single-row",key=f"top_positions_{limit}",
        column_config={
            "Valor USD_num":st.column_config.NumberColumn("Valor USD",format="US$ %.0f"),
            "Peso_num":st.column_config.NumberColumn("Peso",format="%.1f%%"),
            "Variación_num":st.column_config.NumberColumn("Variación",format="%.1f%%"),
            "Estado dato":st.column_config.TextColumn("Estado"),
        }
    )
    try:
        if ev.selection.rows:
            chosen=str(top.iloc[ev.selection.rows[0]]["Ticker"])
            if st.session_state.get("active_ticker")!=chosen:
                st.session_state["active_ticker"]=chosen; st.rerun()
    except Exception: pass

def render_active_context():
    snap=active_ticker_snapshot(st.session_state.get("active_ticker",""))
    if not snap:
        return
    st.markdown("#### Contexto activo")
    c1,c2,c3,c4=st.columns(4)
    c1.metric(snap["Ticker"],snap["Nombre"])
    c2.metric("Valor en cartera",fmt_usd(snap["Valor USD"]))
    c3.metric("Peso",fmt_pct(snap["Peso"]))
    c4.metric("Variación",fmt_pct(snap["Variación"]))
    st.caption(f'{snap["Clase"]} · {snap["Tipo"]} · {snap["Región"]} · {snap["Sector"]} · Custodio(s): {snap["Custodios"] or "—"} · Cuenta(s): {snap["Cuentas"] or "—"}')


def simulate_trade(ticker, operation, amount, funding_mode="Reasignación interna"):
    app_df=data.get("app_feed_v2",pd.DataFrame()).copy()
    if app_df.empty:
        return None

    vals=app_df[["Ticker","Valor USD_num"]].dropna().groupby("Ticker",as_index=False)["Valor USD_num"].sum()
    total=float(vals["Valor USD_num"].sum())
    current=float(vals.loc[vals["Ticker"].astype(str)==str(ticker),"Valor USD_num"].sum())
    cash_before=float(vals.loc[vals["Ticker"].astype(str)=="CASH","Valor USD_num"].sum())

    sign=1 if operation=="Comprar" else -1
    new_value=current+sign*float(amount)
    if new_value < 0:
        return {"error":"La venta supera el valor actual de la posición."}

    internal = funding_mode=="Reasignación interna"
    cash_after=cash_before
    if internal:
        if operation=="Comprar":
            cash_after=cash_before-float(amount)
            if cash_after < -1e-9:
                return {"error":f"La compra requiere {fmt_usd(amount)} pero CASH disponible es {fmt_usd(cash_before)}."}
        else:
            cash_after=cash_before+float(amount)
        new_total=total
    else:
        new_total=total+sign*float(amount)

    if new_total <= 0:
        return {"error":"El patrimonio resultante no es válido."}

    before_weight=current/total if total else 0
    after_weight=new_value/new_total if new_total else 0

    # Update selected ticker.
    mask=vals["Ticker"].astype(str)==str(ticker)
    if mask.any():
        vals.loc[mask,"Valor USD_num"]=new_value
    elif new_value>0:
        vals=pd.concat([vals,pd.DataFrame([{"Ticker":ticker,"Valor USD_num":new_value}])],ignore_index=True)

    # Update CASH only for internal reallocation, unless the simulated ticker itself is CASH.
    if internal and str(ticker)!="CASH":
        cmask=vals["Ticker"].astype(str)=="CASH"
        if cmask.any():
            vals.loc[cmask,"Valor USD_num"]=cash_after
        elif cash_after>0:
            vals=pd.concat([vals,pd.DataFrame([{"Ticker":"CASH","Valor USD_num":cash_after}])],ignore_index=True)

    vals=vals[vals["Valor USD_num"]>0].sort_values("Valor USD_num",ascending=False)
    top5_before=app_df.groupby("Ticker")["Valor USD_num"].sum().sort_values(ascending=False).head(5).sum()/total if total else 0
    top5_after=vals.head(5)["Valor USD_num"].sum()/new_total if new_total else 0

    return {
        "ticker":ticker,"operation":operation,"amount":float(amount),"funding_mode":funding_mode,
        "total_before":total,"total_after":new_total,
        "value_before":current,"value_after":new_value,
        "cash_before":cash_before,"cash_after":cash_after,
        "weight_before":before_weight,"weight_after":after_weight,
        "top5_before":top5_before,"top5_after":top5_after
    }

COMPARISON_HELP={
"P/E":"Cuánto pago por las ganancias actuales",
"Forward P/E":"Cuánto pago por las ganancias futuras esperadas",
"PEG":"El precio es razonable para su crecimiento",
"EV/EBITDA":"Cuánto pago por el negocio en relación con su resultado operativo",
}
def render_company_comparison(result):
    if not result:return
    a=result.get("company_a","Empresa A"); b=result.get("company_b","Empresa B")
    rows=[]
    for m in result.get("metrics",[]):
        name=m.get("indicator","")
        try: va=float(m.get("a")) if m.get("a") is not None else None
        except: va=None
        try: vb=float(m.get("b")) if m.get("b") is not None else None
        except: vb=None
        score=0; winner="Sin ventaja"
        if va and vb and va>0 and vb>0:
            mid=(va+vb)/2
            score=(va-vb)/mid*100 if mid else 0
            if score<-1:winner=a
            elif score>1:winner=b
        rows.append({"Indicador":name,a:va,b:vb,"Ventaja relativa":score,"Favorece":winner,"Qué significa":COMPARISON_HELP.get(name,"")})
    if rows:
        dfc=pd.DataFrame(rows)
        st.subheader(f"Comparación de valuación · {a} vs {b}")
        st.caption("En estos múltiplos, un valor menor suele ser más favorable sólo si las empresas son comparables y los datos son positivos/significativos.")
        fig=px.bar(dfc,x="Ventaja relativa",y="Indicador",orientation="h",
                   custom_data=[a,b,"Favorece","Qué significa"])
        fig.update_traces(hovertemplate="<b>%{y}</b><br>"+a+": %{customdata[0]:.2f}x<br>"+b+": %{customdata[1]:.2f}x<br>Favorece: %{customdata[2]}<br>%{customdata[3]}<extra></extra>")
        fig.add_vline(x=0,line_width=1)
        fig.update_layout(height=330,xaxis_title=f"← favorece {a}   |   favorece {b} →",yaxis_title=None)
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(dfc[["Indicador",a,b,"Favorece"]],hide_index=True,use_container_width=True)
        fa=(dfc["Favorece"]==a).sum(); fb=(dfc["Favorece"]==b).sum(); fn=(dfc["Favorece"]=="Sin ventaja").sum()
        st.caption(f"Lectura rápida de estos múltiplos: {a} favorecido en {fa}, {b} en {fb}, sin ventaja clara en {fn}. Esto no constituye un ganador global.")
        with st.expander("Ayuda memoria de indicadores"):
            for k,v in COMPARISON_HELP.items(): st.markdown(f"**{k}** — {v}")
    if result.get("analysis"):
        st.markdown("### Lectura del asesor")
        st.markdown(result["analysis"])

st.title(page)
if page in ["Resumen","Diversificación","Evolución","Riesgo","Custodia","Posiciones"]:
    st.caption("Dashboard analítico de PMS Max · navegación, filtros, drill-down y contexto compartido")

if page=="Resumen":
    render_global_context_banner()
    cols=st.columns([1.55,1.0,1.0,0.9])
    with cols[0]:
        metric_card("Patrimonio total",fmt_usd(summary["total"]),"Incluye Crypto",summary.get("total_change"))
    with cols[1]:
        metric_card("Argentina",fmt_pct(summary["argentina_pct"]),"Exposición",summary.get("argentina_change"))
    with cols[2]:
        metric_card("Top 5",fmt_pct(summary["top5_pct"]),"Concentración",summary.get("top5_change"))
    with cols[3]:
        metric_card("Posiciones",str(int(summary["positions_count"])),f"Precios: {summary.get('price_update') if summary.get('price_update') not in ('nan','NaN','') else '—'}",None)

    c1,c2=st.columns([0.8,1.2])
    with c1:
        st.subheader("Composición por clase")
        df=data["dashboard_diversificacion_v2"].copy()
        df=df[(df["Clase inversión"]!="Total")&df["Clase inversión"].notna()]
        fig=px.bar(df,x="Valor USD_num",y="Clase inversión",orientation="h",hover_data={"Peso_num":":.1%"},labels={"Valor USD_num":"Valor USD","Clase inversión":"Clase"})
        fig.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        st.subheader("Mayores movimientos")
        app=data["app_feed_v2"].copy()
        m=app[app["Ticker"].notna()].copy()
        m["abs"]=m["Variación_num"].abs()
        m=m.sort_values("abs",ascending=False).head(10)
        m_show=m[["Ticker","Nombre","Valor USD_num","Peso_num","Variación_num","Estado dato"]].copy()
        m_show["Nombre"]=m_show["Nombre"].map(compact_name)
        m_show["Estado dato"]=m_show["Estado dato"].map(compact_status)
        m_show["Peso_num"]=pct_points(m_show["Peso_num"])
        m_show["Variación_num"]=pct_points(m_show["Variación_num"])
        st.dataframe(
            m_show,
            hide_index=True,use_container_width=True,
            column_config={
                "Valor USD_num":st.column_config.NumberColumn("Valor USD",format="US$ %.0f"),
                "Peso_num":st.column_config.NumberColumn("Peso",format="%.1f%%"),
                "Variación_num":st.column_config.NumberColumn("Variación",format="%.1f%%"),
                "Nombre":st.column_config.TextColumn("Nombre",width="medium"),
                "Estado dato":st.column_config.TextColumn("Estado",width="small"),
            }
        )

    with st.expander("Control de consistencia"):
        app_df=data.get("app_feed_v2",pd.DataFrame())
        look_df=data.get("looker_feed_v2",pd.DataFrame())
        app_total=float(app_df["Valor USD_num"].sum()) if not app_df.empty and "Valor USD_num" in app_df.columns else 0.0
        look_total=float(look_df["Valor USD_num"].sum()) if not look_df.empty and "Valor USD_num" in look_df.columns else 0.0
        diff=look_total-app_total
        q1,q2,q3=st.columns(3)
        q1.metric("Total app feed",fmt_usd(app_total))
        q2.metric("Total detalle",fmt_usd(look_total))
        q3.metric("Diferencia",fmt_usd(diff))
        if abs(diff)<=1:
            st.success("Reconciliación de feeds: OK")
        else:
            st.warning("Los feeds no reconcilian exactamente; revisar antes de interpretar diferencias pequeñas como rendimiento.")

    st.subheader("Principales posiciones")
    st.caption("Seleccioná una fila para convertir ese activo en el ticker activo.")
    top_positions_table(12)

elif page=="Diversificación":
    render_global_context_banner()
    ex=data["dashboard_exposicion_v2"].copy()
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### Región")
        r=ex[["Región","Valor USD_num","Peso_num"]].dropna(subset=["Región"]).sort_values("Valor USD_num",ascending=True)
        fig=px.bar(
            r,x="Valor USD_num",y="Región",orientation="h",hover_data={"Peso_num":":.1%"},
            labels={"Valor USD_num":"Valor USD"},
            color_discrete_sequence=["#79bff2"]
        )
        fig.update_layout(yaxis_title=None)
        ev=st.plotly_chart(fig,use_container_width=True,on_select="rerun",selection_mode="points",key="region_chart")
        try:
            pts=ev.selection.points
            if pts:
                set_context("Región",pts[0].get("y"))
        except Exception: pass
    with c2:
        st.markdown("### Sector")
        s=ex[["Sector","Sector Valor USD_num","Sector Peso_num"]].dropna(subset=["Sector"]).sort_values("Sector Valor USD_num",ascending=True)
        fig=px.bar(
            s,x="Sector Valor USD_num",y="Sector",orientation="h",hover_data={"Sector Peso_num":":.1%"},
            labels={"Sector Valor USD_num":"Valor USD"},
            color_discrete_sequence=["#4f8fc7"]
        )
        fig.update_layout(yaxis_title=None)
        ev2=st.plotly_chart(fig,use_container_width=True,on_select="rerun",selection_mode="points",key="sector_chart")
        try:
            pts=ev2.selection.points
            if pts:
                set_context("Sector",pts[0].get("y"))
        except Exception: pass
    st.caption("Click en una barra para convertir esa exposición en contexto global. El Asesor IA recibe ese mismo contexto.")
    detail=apply_analysis_context(data.get("looker_feed_v2",pd.DataFrame()).copy())
    if not detail.empty and st.session_state.get("analysis_context",{}).get("value"):
        st.subheader("Posiciones directas dentro del contexto")
        st.caption("El gráfico de exposición puede incluir ETF look-through agregado; esta tabla muestra posiciones directas y por eso puede no reconciliar 1:1 con el gráfico.")
        detail_show=detail.sort_values("Valor USD_num",ascending=False)[["Ticker","Nombre","Custodio","Cuenta","Clase","Tipo","Región directa","Sector directo","Valor USD_num","Peso cartera_num"]].copy()
        detail_show["Peso cartera_num"]=pct_points(detail_show["Peso cartera_num"])
        st.dataframe(
            detail_show,
            hide_index=True,use_container_width=True,
            column_config={
                "Valor USD_num":st.column_config.NumberColumn("Valor USD",format="US$ %.0f"),
                "Peso cartera_num":st.column_config.NumberColumn("Peso cartera",format="%.1f%%"),
            }
        )


    st.markdown("### Cripto vs cartera convencional")
    total_port = float(summary["total"]) if pd.notna(summary.get("total")) else 0.0
    crypto_port = float(summary["crypto"]) if pd.notna(summary.get("crypto")) else 0.0
    conventional_port = max(total_port - crypto_port, 0.0)
    pie_df = pd.DataFrame({
        "Segmento":["Crypto","Cartera convencional"],
        "Valor USD":[crypto_port, conventional_port]
    })
    pie_df["Peso"] = pie_df["Valor USD"] / pie_df["Valor USD"].sum() if pie_df["Valor USD"].sum() else 0.0
    fig = px.pie(
        pie_df,
        names="Segmento",
        values="Valor USD",
        hole=0.52,
        color="Segmento",
        color_discrete_map={
            "Crypto":"#5d1f35",
            "Cartera convencional":"#5b8ecb"
        },
    )
    fig.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>US$ %{value:,.0f}<br>%{percent}",
        hovertemplate="<b>%{label}</b><br>Valor: US$ %{value:,.0f}<br>Peso: %{percent}<extra></extra>"
    )
    fig.update_layout(
        height=380,
        margin=dict(l=10,r=10,t=10,b=10),
        legend_title_text="",
    )
    st.plotly_chart(fig,use_container_width=True)

elif page=="Evolución":
    evo=data["dashboard_evolucion_v2"].copy()
    hist=evo[evo["Valor total USD_num"].gt(0)].copy()
    fig=px.line(hist,x="Fecha",y="Valor total USD_num",markers=True,labels={"Valor total USD_num":"Patrimonio USD"})
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Patrimonio observado; todavía no se interpreta como retorno. Evolución queda pendiente de una versión más dinámica y representativa.")
    st.subheader("Top 15 activos")
    app=data["app_feed_v2"].copy()
    top=app[app["Ticker"].notna()].sort_values("Valor USD_num",ascending=False).head(15).copy()
    top["Cotización"]=top.apply(quote_text,axis=1)
    st.dataframe(top[["Ticker","Nombre","Valor USD_num","Peso_num","Cotización","Variación_num","Estado dato"]],hide_index=True,use_container_width=True)

elif page=="Riesgo":
    render_global_context_banner()
    risk=data["dashboard_riesgo_v2"].copy()
    show=risk[risk["Métrica"].isin(["Mayor posición","Top 5 posiciones","Top 10 posiciones","HHI cartera","Peso Crypto","Exposición Argentina"])]
    cols=st.columns(max(1,len(show)))
    for c,(_,r) in zip(cols,show.iterrows()):
        with c: st.metric(r["Métrica"],r["Valor"])
    stress=risk[risk["Métrica"].isin(["Argentina","Crypto","Tecnología / Nasdaq proxy","Combinado"])].copy()
    if not stress.empty:
        impact_usd_col=next((c for c in stress.columns if c.strip().lower() in ["impacto usd_num","impacto usd"]),None)
        impact_pct_col=next((c for c in stress.columns if c.strip().lower() in ["impacto cartera_num","impacto cartera %_num","impacto cartera %"]),None)

        if impact_usd_col:
            if impact_usd_col=="Impacto USD":
                stress["_impact_usd"]=stress[impact_usd_col].map(local_num)
                impact_usd_col="_impact_usd"
            stress=stress.sort_values(impact_usd_col,ascending=True)
            fig=px.bar(
                stress,x=impact_usd_col,y="Métrica",orientation="h",
                labels={impact_usd_col:"Impacto USD"},
                color_discrete_sequence=["#d06a74"]
            )
            st.plotly_chart(fig,use_container_width=True)
        elif impact_pct_col:
            tmp=stress.copy()
            if "%" in impact_pct_col and not impact_pct_col.endswith("_num"):
                tmp["_impact_pct"]=tmp[impact_pct_col].map(local_num)
            else:
                tmp["_impact_pct"]=pd.to_numeric(tmp[impact_pct_col],errors="coerce")*100
            tmp=tmp.sort_values("_impact_pct",ascending=True)
            fig=px.bar(
                tmp,x="_impact_pct",y="Métrica",orientation="h",
                labels={"_impact_pct":"Impacto cartera (%)"},
                color_discrete_sequence=["#d06a74"]
            )
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("Stress test disponible, pero la fuente no expone una columna de impacto graficable.")
    pending=risk[risk["Estado"].eq("HISTORIAL INSUFICIENTE")]
    if not pending.empty:
        st.subheader("Métricas aún no maduras")
        st.dataframe(pending[["Métrica","Estado","Interpretación"]],hide_index=True,use_container_width=True)

    st.subheader("Concentración por posición")
    top_positions_table(15)

elif page=="Custodia":
    summ=data["app_custodia_resumen_v2"].copy()
    detail=data["app_custodia_detalle_v2"].copy()
    cust_options=["TODOS"]+summ["Custodio"].dropna().astype(str).tolist()
    cust=st.selectbox("Custodio",cust_options,index=0)

    if cust=="TODOS":
        st.session_state["analysis_context"]={"dimension":"","value":""}
        total_val=float(summ["Valor USD_num"].sum()) if "Valor USD_num" in summ.columns else float(detail["Valor USD_num"].sum())
        total_accounts=int(summ["Cantidad cuentas_num"].sum()) if "Cantidad cuentas_num" in summ.columns else int(detail["Cuenta"].nunique())
        a,b,c=st.columns(3)
        a.metric("Valor",fmt_usd(total_val))
        b.metric("Peso cartera","100,0%")
        c.metric("Cuentas",total_accounts)
        rows=detail.copy().sort_values("Valor USD_num",ascending=False)
    else:
        st.session_state["analysis_context"]={"dimension":"Custodio","value":cust}
        s=summ[summ["Custodio"]==cust].iloc[0]
        a,b,c=st.columns(3)
        a.metric("Valor",fmt_usd(s["Valor USD_num"]))
        b.metric("Peso cartera",fmt_pct(s["Peso cartera_num"]))
        c.metric("Cuentas",int(s["Cantidad cuentas_num"]))
        rows=detail[detail["Custodio"]==cust].copy().sort_values("Valor USD_num",ascending=False)

    fig=px.bar(
        rows.head(15),x="Valor USD_num",y="Ticker",color="Cuenta",orientation="h",
        labels={"Valor USD_num":"Valor USD"}
    )
    st.plotly_chart(fig,use_container_width=True)
    rows_show=rows[["Cuenta","Ticker","Nombre","Tipo","Clase","Valor USD_num","Peso custodio_num"]].copy()
    rows_show["Peso custodio_num"]=pct_points(rows_show["Peso custodio_num"])
    st.dataframe(
        rows_show,hide_index=True,use_container_width=True,
        column_config={
            "Valor USD_num":st.column_config.NumberColumn("Valor USD",format="US$ %.0f"),
            "Peso custodio_num":st.column_config.NumberColumn("Peso custodio",format="%.1f%%"),
        }
    )

elif page=="Posiciones":
    mode=st.segmented_control("Vista",["Consolidado","Por cuenta"],default="Consolidado")
    search=st.text_input("Buscar ticker o nombre")
    view=filtered.copy()
    if search:
        q=search.lower().strip()
        view=view[view["Ticker"].astype(str).str.lower().str.contains(q,na=False)|view["Nombre"].astype(str).str.lower().str.contains(q,na=False)]
    if mode=="Consolidado":
        # One row per ticker. Keep a compact list of accounts instead of duplicated rows.
        agg=view.groupby("Ticker",as_index=False).agg({
            "Nombre":"first","Tipo":"first","Valor USD_num":"sum",
            "Variación_num":"first","Estado dato":"first",
            "Cuenta":lambda s:", ".join(sorted(set(str(x) for x in s if pd.notna(x))))
        })
        total_base=float(data.get("app_feed_v2",pd.DataFrame()).get("Valor USD_num",pd.Series(dtype=float)).sum())
        agg["Peso cartera_num"]=agg["Valor USD_num"]/total_base if total_base else 0.0
        view=agg.sort_values("Valor USD_num",ascending=False)
    else:
        view=view.sort_values("Valor USD_num",ascending=False)

    st.caption(f"{len(view)} filas · {fmt_usd(view['Valor USD_num'].sum())}")
    view_show=view[["Ticker","Nombre","Cuenta","Tipo","Valor USD_num","Peso cartera_num","Variación_num","Estado dato"]].copy()
    view_show["Peso cartera_num"]=pct_points(view_show["Peso cartera_num"])
    view_show["Variación_num"]=pct_points(view_show["Variación_num"])
    pos_event=st.dataframe(
        view_show,
        hide_index=True,use_container_width=True,height=700,
        on_select="rerun",selection_mode="single-row",key="positions_table",
        column_config={
            "Valor USD_num":st.column_config.NumberColumn("Valor USD",format="US$ %.0f"),
            "Peso cartera_num":st.column_config.NumberColumn("Peso",format="%.2f%%"),
            "Variación_num":st.column_config.NumberColumn("Variación",format="%.1f%%"),
            "Estado dato":st.column_config.TextColumn("Estado"),
        }
    )
    try:
        selected_rows=pos_event.selection.rows
        if selected_rows:
            chosen=view.iloc[selected_rows[0]]["Ticker"]
            if chosen and st.session_state.get("active_ticker")!=chosen:
                st.session_state["active_ticker"]=str(chosen)
                st.rerun()
    except Exception:
        pass


elif page=="Comparador":
    st.subheader("Comparador de empresas")
    st.caption("Herramienta analítica independiente del chat. Usa datos externos actuales y contexto de PMS Max.")
    render_active_context()

    c1,c2=st.columns(2)
    t1=c1.text_input("Ticker 1",value=st.session_state.get("active_ticker",""),placeholder="GOOGL",key="cmp_t1")
    t2=c2.text_input("Ticker 2",placeholder="MSFT",key="cmp_t2")
    if t1 and t2 and st.button("Comparar empresas",type="primary",key="cmp_btn"):
        with st.spinner("Consultando valuación y fundamentales…"):
            st.session_state["last_company_comparison"]=compare_companies_structured(
                t1,t2,data,filtered,
                analysis_context=st.session_state.get("analysis_context",{})
            )
    if st.session_state.get("last_company_comparison"):
        render_company_comparison(st.session_state["last_company_comparison"])

elif page=="Simulador":
    st.subheader("Simulador de operación")
    st.caption("Cálculo determinístico sobre la cartera actual. No ejecuta operaciones.")
    render_active_context()

    tickers=sorted(data.get("app_feed_v2",pd.DataFrame()).get("Ticker",pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    active=st.session_state.get("active_ticker","")
    idx=tickers.index(active) if active in tickers else 0
    c1,c2,c3,c4=st.columns([1,1,1,1.35])
    ticker=c1.selectbox("Ticker",tickers,index=idx if tickers else 0,key="sim_ticker") if tickers else ""
    operation=c2.selectbox("Operación",["Comprar","Vender"],key="sim_op")
    amount=c3.number_input("Monto USD",min_value=0.0,step=100.0,key="sim_amount")
    funding_mode=c4.selectbox(
        "Origen / destino",
        ["Reasignación interna","Aporte / retiro externo"],
        help="Reasignación interna usa o genera CASH y mantiene constante el patrimonio total. Aporte/retiro modifica el patrimonio."
    )

    if ticker and amount>0:
        sim=simulate_trade(ticker,operation,amount,funding_mode=funding_mode)
        if sim and sim.get("error"):
            st.error(sim["error"])
        elif sim:
            a,b,c,d,e=st.columns(5)
            a.metric("Valor posición",fmt_usd(sim["value_after"]),delta=fmt_usd(sim["value_after"]-sim["value_before"]))
            b.metric("Peso posición",fmt_pct(sim["weight_after"]),delta=f'{(sim["weight_after"]-sim["weight_before"])*100:+.2f} pp')
            c.metric("CASH",fmt_usd(sim["cash_after"]),delta=fmt_usd(sim["cash_after"]-sim["cash_before"]) if sim["funding_mode"]=="Reasignación interna" else "sin efecto directo")
            d.metric("Patrimonio total",fmt_usd(sim["total_after"]),delta=fmt_usd(sim["total_after"]-sim["total_before"]))
            e.metric("Top 5",fmt_pct(sim["top5_after"]),delta=f'{(sim["top5_after"]-sim["top5_before"])*100:+.2f} pp')

            st.markdown("#### Antes vs. después")
            simdf=pd.DataFrame([
                {"Métrica":"Valor posición","Antes":sim["value_before"],"Después":sim["value_after"],"Unidad":"USD"},
                {"Métrica":"Peso posición","Antes":sim["weight_before"]*100,"Después":sim["weight_after"]*100,"Unidad":"%"},
                {"Métrica":"Top 5","Antes":sim["top5_before"]*100,"Después":sim["top5_after"]*100,"Unidad":"%"},
            ])
            fig=px.bar(simdf,x="Métrica",y=["Antes","Después"],barmode="group")
            st.plotly_chart(fig,use_container_width=True)

            if st.button("Pedir lectura al Asesor IA",key="sim_to_ai"):
                st.session_state["force_page"]="Asesor IA"
                st.session_state["pending_advisor_prompt"]=(
                    f"Analizá esta simulación ({funding_mode}): {operation.lower()} US$ {amount:.0f} de {ticker}. "
                    f"El peso pasa de {fmt_pct(sim['weight_before'])} a {fmt_pct(sim['weight_after'])}; "
                    f"Top 5 pasa de {fmt_pct(sim['top5_before'])} a {fmt_pct(sim['top5_after'])}. "
                    "Quiero riesgos, concentración y contradicciones con la cartera actual."
                )
                st.rerun()

elif page=="Asesor IA":
    st.subheader("Asesor IA")
    st.caption("Conversación libre y análisis contextual. Comparador y Simulador también tienen páginas propias.")
    try:
        advisor_ready=bool(st.secrets.get("OPENAI_API_KEY",""))
    except Exception:
        advisor_ready=False
    if not advisor_ready:
        st.warning("El Asesor IA todavía no está activado. El Dashboard y las herramientas determinísticas funcionan normalmente; la IA se habilita agregando OPENAI_API_KEY en Streamlit Secrets.")
    ctx=st.session_state.get("analysis_context",{"dimension":"","value":""})
    if ctx.get("value"):
        st.success(f'Contexto analítico activo: {ctx.get("dimension")} · {ctx.get("value")}')
    render_active_context()
    action=st.selectbox("Acción guiada",["Consulta libre","Analizar cartera","Analizar ticker","Comparar empresas","Consultar fundamentales","Consultar noticias","Explicar movimiento","Simular operación"])
    action_prompt=None
    if action in ["Analizar ticker","Consultar fundamentales","Consultar noticias","Explicar movimiento"]:
        ticker=st.text_input("Ticker",value=st.session_state.get("active_ticker",""),placeholder="Ej: GOOGL")
        if ticker and st.button("Ejecutar análisis",type="primary"):
            action_prompt=build_action_prompt(action,{"ticker":ticker})
    elif action=="Comparar empresas":
        c1,c2=st.columns(2)
        t1=c1.text_input("Ticker 1",value=st.session_state.get("active_ticker",""),placeholder="GOOGL")
        t2=c2.text_input("Ticker 2",placeholder="MSFT")
        if t1 and t2 and st.button("Comparar",type="primary"):
            with st.spinner("Consultando valuación, fundamentales y contexto de cartera…"):
                st.session_state["last_company_comparison"]=compare_companies_structured(t1,t2,data,filtered,analysis_context=st.session_state.get("analysis_context",{}))
        if st.session_state.get("last_company_comparison"):
            render_company_comparison(st.session_state["last_company_comparison"])
    elif action=="Simular operación":
        c1,c2,c3=st.columns(3); ticker=c1.text_input("Ticker",value=st.session_state.get("active_ticker","")); op=c2.selectbox("Operación",["Comprar","Vender"]); amount=c3.number_input("Monto USD",min_value=0.0,step=100.0)
        if ticker and amount>0 and st.button("Simular",type="primary"):
            action_prompt=build_action_prompt(action,{"ticker":ticker,"operation":op,"amount":amount})
    elif action=="Analizar cartera":
        if st.button("Analizar cartera",type="primary"):
            action_prompt=build_action_prompt(action,{})

    if "messages" not in st.session_state: st.session_state.messages=[]
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    prompt=st.chat_input("Preguntale al asesor…")
    pending=st.session_state.pop("pending_advisor_prompt",None)
    user_prompt=pending or action_prompt or prompt
    if user_prompt:
        st.session_state.messages.append({"role":"user","content":user_prompt})
        with st.chat_message("user"): st.markdown(user_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analizando…"):
                answer=ask_advisor(user_prompt,data,filtered,st.session_state.messages[-8:],selected_ticker=st.session_state.get("active_ticker",""),analysis_context=st.session_state.get("analysis_context",{}))
            st.markdown(answer)
        st.session_state.messages.append({"role":"assistant","content":answer})
