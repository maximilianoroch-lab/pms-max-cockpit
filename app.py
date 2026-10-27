from pms_shared_ui import style_bar as shared_style_bar, fmt_usd as shared_fmt_usd, fmt_pct_fraction as shared_fmt_pct, fmt_number as shared_fmt_number, finish_executive_bar

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
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {color: #e5edf6 !important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color: #a9bfd3 !important;}
[data-testid="stSidebar"] [role="radiogroup"] p {color: #e5edf6 !important;}
/* Sidebar dark palette: readable text across Streamlit widget internals. */
[data-testid="stSidebar"] {color: #e8f1fb !important; color-scheme: dark;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
[data-testid="stSidebar"] [data-testid="stText"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stSidebar"] div[data-testid="stRadio"] label,
[data-testid="stSidebar"] div[data-testid="stRadio"] label *,
[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] label * {color: #e8f1fb !important; -webkit-text-fill-color: #e8f1fb !important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {color: #adc4da !important; -webkit-text-fill-color: #adc4da !important;}
[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {background-color: #15334e; border-radius: 7px;}

[data-testid="stDataFrame"] {font-size: 0.92rem;}
.metric-card {background:linear-gradient(180deg,#0d1b2b,#0a1827);border:1px solid #28455f;border-radius:14px;padding:14px 16px;min-height:112px}
.metric-label{color:#93a7bd;font-size:12px;font-weight:700;text-transform:uppercase}
.metric-value{color:#f4f7fb;font-size:24px;font-weight:900;margin-top:6px;white-space:nowrap}
.metric-sub{color:#93a7bd;font-size:11px;margin-top:6px}
.up{color:#54d49a;font-weight:800}.down{color:#ff7a7a;font-weight:800}.flat{color:#93a7bd;font-weight:800}
.st-key-simulator_metrics [data-testid="stMetricValue"] {font-size:clamp(1.35rem,2vw,1.9rem);white-space:normal;overflow-wrap:anywhere;}
.st-key-simulator_metrics [data-testid="stMetricDelta"] {font-size:.92rem;}
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
    colmap={"Región":"Región directa","Sector":"Sector directo","Custodio":"Custodio","Tipo":"Tipo"}
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
        key="dashboard_nav",
        on_change=lambda: (st.session_state.pop("force_page",None),st.session_state.update(tools_nav="—"))
    )
    st.markdown("### Herramientas")
    st.markdown("""<style>[data-testid="stSidebar"] [data-testid="stRadio"] label p {white-space:nowrap; font-size:0.91rem}</style>""",unsafe_allow_html=True)
    tool_page=st.radio(
        "Herramientas",
        ["—","Comparar Activos","Simular Compra/Venta"],
        label_visibility="collapsed",
        key="tools_nav",
        on_change=lambda: st.session_state.pop("force_page",None)
    )
    st.markdown("### IA")
    ai_open=st.button("Asesor IA",width='stretch')
    if ai_open:
        # Los widgets dashboard_nav/tools_nav ya están instanciados en este rerun.
        # No modificar sus keys directamente: StreamlitWidgetAlreadyInstantiatedError.
        st.session_state["force_page"]="Asesor IA"
    if tool_page!="—":
        page={"Comparar Activos":"Comparar","Simular Compra/Venta":"Simulador"}.get(tool_page,tool_page)
    if st.session_state.get("force_page")=="Asesor IA":
        page="Asesor IA"
    st.divider()
    # El ticker activo es contexto para el Asesor, no un filtro de actualización.
    filtered=positions.copy()
    if not positions.empty:
        all_tickers=sorted(positions["Ticker"].dropna().astype(str).unique().tolist())
        active_default=st.session_state.get("active_ticker","")
        ticker_options=["—"]+all_tickers
        ticker_index=ticker_options.index(active_default) if active_default in ticker_options else 0
        selected_ticker=st.selectbox("Ticker activo (Asesor IA)",ticker_options,index=ticker_index,
            help="El ticker seleccionado se comparte con el Asesor IA. No limita los datos que se actualizan.")
        st.session_state["active_ticker"]="" if selected_ticker=="—" else selected_ticker
    else:
        st.session_state["active_ticker"]=""
    ctx=st.session_state.get("analysis_context",{"dimension":"","value":""})
    if ctx.get("value"):
        st.info(f'Contexto: {ctx.get("dimension")} · {ctx.get("value")}')
        if st.button("Limpiar contexto",width='stretch'):
            st.session_state["analysis_context"]={"dimension":"","value":""}
            st.rerun()

    st.caption("La actualización recarga todas las fuentes y todas las posiciones.")
    if st.button("Actualizar toda la cartera",width='stretch'):
        st.cache_data.clear(); st.rerun()
    st.caption(f'Fuente: {PORTFOLIO["display_name"]} · {summary.get("last_market","—")}')
    try: has_key=bool(st.secrets.get("OPENAI_API_KEY",""))
    except Exception: has_key=False
    if has_key:
        try: active_model=st.secrets.get("OPENAI_MODEL","gpt-5.6")
        except Exception: active_model="gpt-5.6"
        st.caption(f"Asesor IA: configurado · {active_model}")
    else:
        st.caption("Asesor IA: pendiente de API key")


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

def table_money(df, columns=("Valor USD_num", "Valor total USD_num", "Cambio USD")):
    """Prepara copia de presentación: el origen conserva números para cálculos y selección."""
    show=df.copy()
    for col in columns:
        if col in show.columns:
            show[col]=show[col].map(lambda v:fmt_usd(v) if pd.notna(v) else "—")
    return show

def colored_variation(df, column="Variación_num"):
    """Resalta variaciones con colores, conservando números para ordenar/seleccionar."""
    show=table_money(df)
    if column not in show.columns:
        return show
    def color(v):
        try:
            x=float(v)
            if pd.isna(x):return ""
            return "color: #43d59c; font-weight: 700" if x>0 else ("color: #ff7070; font-weight: 700" if x<0 else "color: #9aacc0")
        except (TypeError,ValueError):
            return ""
    return show.style.map(color,subset=[column])

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
    if v is None:
        return '<span class="flat">—</span>'
    try:x=float(v)
    except:return '<span class="flat">—</span>'
    if x>0:return f'<span class="up">▲ +{x*100:.1f}%</span>'
    if x<0:return f'<span class="down">▼ {x*100:.1f}%</span>'
    return '<span class="flat">→ 0,0%</span>'

# Color institucional: puede variarse brillo, pero nunca su identidad de base.
CUSTODIAN_COLORS = {
    "CRITERIA": "#9CA5B1", "BINANCE": "#D4AA28",
    "ADCAP": "#74AE52", "BBVA": "#3678BC",
    "IOL": "#8EB7D9", "GALICIA": "#D88A42",
    "SANTANDER": "#CC4C4C",
}

def custodian_color(custodian):
    return CUSTODIAN_COLORS.get(str(custodian).strip().upper(), "#748CA5")

def style_bar(fig, horizontal=True):
    return shared_style_bar(fig, horizontal=horizontal)

def signed_number(v, percentage=False):
    if v is None or pd.isna(v): return "—"
    n=float(v)
    if percentage:
        displayed=round(n,1)
        return ("+" if displayed>0 else "") + f"{displayed:.1f}%".replace(".",",")
    rounded=round(n)
    return ("+" if rounded>0 else "") + fmt_usd(rounded)

def signed_color(v):
    if v is None or pd.isna(v): return "color: #93a7bd"
    n=float(v)
    return "color: #5fc89c" if n>0 else ("color: #f07878" if n<0 else "color: #93a7bd")


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
        colored_variation(top_show),
        hide_index=True,width='stretch',on_select="rerun",selection_mode="single-row",key=f"top_positions_{limit}",
        column_config={
            "Valor USD_num":st.column_config.TextColumn("Valor USD"),
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
    with c1:
        st.caption(snap["Ticker"])
        st.markdown(f'<div style="font-size:clamp(1.05rem,1.45vw,1.45rem);line-height:1.35;overflow-wrap:anywhere;white-space:normal">{__import__("html").escape(str(snap["Nombre"]))}</div>',unsafe_allow_html=True)
    c2.metric("Valor en cartera",fmt_usd(snap["Valor USD"]))
    c3.metric("Peso",fmt_pct(snap["Peso"]))
    c4.metric("Variación",fmt_pct(snap["Variación"]),delta=None)
    # El valor destacado cambia de color según su signo mediante HTML.
    st.markdown(f'<div class="{("up" if snap["Variación"]>0 else "down" if snap["Variación"]<0 else "flat")}">{change_html(snap["Variación"])}</div>',unsafe_allow_html=True)
    st.caption(f'{snap["Tipo"]} · {snap["Región"]} · {snap["Sector"]} · Custodio(s): {snap["Custodios"] or "—"} · Cuenta(s): {snap["Cuentas"] or "—"}')


def simulate_trade(ticker, operation, amount, funding_mode="CASH", source_ticker=None, cash_amount=0.0):
    """Side-effect-free simulation using the same validated engine as DEMO."""
    app_df=data.get("app_feed_v2",pd.DataFrame()).copy()
    if app_df.empty:
        return None
    vals=app_df.groupby("Ticker",as_index=False)["Valor USD_num"].sum()
    holdings=dict(zip(vals["Ticker"].astype(str), vals["Valor USD_num"].astype(float)))
    from pms_trade import simulate_portfolio_trade
    return simulate_portfolio_trade(holdings,ticker,operation,amount,funding_mode,source_ticker,cash_amount)

COMPARISON_HELP={
    "P/E":"Precio respecto de ganancias actuales",
    "Forward P/E":"Precio respecto de ganancias esperadas",
    "PEG":"Valuación relativa al crecimiento de utilidades",
    "EV/EBITDA":"Valor de la empresa respecto del resultado operativo",
    "ROE":"Rentabilidad sobre patrimonio",
    "ROA":"Rentabilidad sobre activos; especialmente útil en bancos",
    "ROIC":"Rentabilidad sobre capital invertido",
    "Crecimiento ingresos 3-5a":"Crecimiento anualizado de ingresos en 3–5 años",
    "Crecimiento EPS 3-5a":"Crecimiento anualizado de utilidad por acción en 3–5 años",
    "Free Cash Flow":"Caja disponible después de inversiones",
    "NIM":"Margen neto de intereses (bancos)",
    "Morosidad":"Proporción de créditos en mora (bancos)",
    "Cobertura mora":"Provisiones frente a cartera en mora (bancos)",
    "Ratio eficiencia":"Costos operativos respecto de ingresos (bancos)",
    "Capital regulatorio":"Capital regulatorio disponible (bancos)"
}
LOWER_BETTER={"P/E","Forward P/E","PEG","EV/EBITDA","Morosidad","Ratio eficiencia"}
HIGHER_BETTER={"ROE","ROA","ROIC","Crecimiento ingresos 3-5a","Crecimiento EPS 3-5a",
               "Free Cash Flow","NIM","Cobertura mora","Capital regulatorio"}

# Claves estables para que variaciones del nombre que devuelve la IA no alteren «Favorece».
def comparison_metric_key(name):
    import unicodedata, re
    text=unicodedata.normalize('NFKD',str(name)).encode('ascii','ignore').decode().lower()
    text=re.sub(r'\s+',' ',text).strip()
    if 'forward' in text and ('p/e' in text or 'pe ' in text): return 'Forward P/E'
    if 'peg' in text: return 'PEG'
    if 'ev/ebitda' in text or 'ev / ebitda' in text: return 'EV/EBITDA'
    if 'roic' in text: return 'ROIC'
    if 'roe' in text or 'return on equity' in text: return 'ROE'
    if 'roa' in text or 'return on assets' in text: return 'ROA'
    if 'p/e' in text or text=='pe': return 'P/E'
    if 'tier' in text or 'cet1' in text or 'capital regulatorio' in text: return 'Capital regulatorio'
    if 'cobertura' in text and ('mora' in text or 'cartera' in text): return 'Cobertura mora'
    if 'morosidad' in text or 'cartera irregular' in text or 'npl' in text: return 'Morosidad'
    if 'eficiencia' in text or 'cost-to-income' in text: return 'Ratio eficiencia'
    if 'nim' in text or 'margen financiero' in text or 'margen neto de intereses' in text: return 'NIM'
    if 'crecimiento' in text and ('eps' in text or 'utilidad por accion' in text or 'beneficio por accion' in text): return 'Crecimiento EPS 3-5a'
    if 'crecimiento' in text and ('venta' in text or 'ingres' in text): return 'Crecimiento ingresos 3-5a'
    if 'free cash flow' in text or 'flujo de caja libre' in text or text=='fcf': return 'Free Cash Flow'
    return None

COMPARISON_HELP.update({
    'ROE':'Rentabilidad del banco sobre el patrimonio de los accionistas; verificar si está anualizado.',
    'ROA':'Rentabilidad sobre los activos del banco; verificar si está anualizado.',
    'NIM':'Margen neto de intereses: ingreso financiero neto respecto de activos remunerados; las metodologías pueden variar.',
    'Morosidad':'Porcentaje de préstamos con atrasos o incumplimientos; cuanto menor, mejor, si las definiciones coinciden.',
    'Cobertura mora':'Provisiones constituidas frente a créditos en mora; no equivale a garantías reales.',
    'Ratio eficiencia':'Gastos operativos sobre ingresos; menor suele ser mejor si las bases son equivalentes.',
    'Capital regulatorio':'Tier 1 es capital regulatorio de alta calidad; CET1 es su componente de capital ordinario de máxima calidad. No confundir ambos ratios.',
})

def render_company_comparison(result):
    if not result:return
    a=result.get("company_a","Empresa A"); b=result.get("company_b","Empresa B")
    rows=[]
    for m in result.get("metrics",[]):
        name=str(m.get("indicator","")).strip()
        if not name or m.get("relevant") is False:
            continue
        try: va=float(m.get("a")) if m.get("a") is not None else None
        except (TypeError,ValueError): va=None
        try: vb=float(m.get("b")) if m.get("b") is not None else None
        except (TypeError,ValueError): vb=None
        # Omitir métricas que no aplican a este tipo de empresa.
        if va is None and vb is None:continue
        key=comparison_metric_key(name)
        winner="Sin ventaja clara"
        comparable=m.get("comparable",True) is not False
        if va is not None and vb is not None and key:
            denom=max(abs(va),abs(vb),1e-9)
            if abs(va-vb)/denom>=0.01:
                if key in LOWER_BETTER and va>0 and vb>0:
                    winner=a if va<vb else b
                elif key in HIGHER_BETTER:
                    winner=a if va>vb else b
        # La diferencia numérica no acredita comparabilidad: no adjudicar un
        # ganador cuando las definiciones o períodos declarados difieren.
        if not comparable:
            winner="No comparable: criterios distintos"
        period_a=str(m.get("period_a") or m.get("a_period") or "").strip()
        period_b=str(m.get("period_b") or m.get("b_period") or "").strip()
        source_a=str(m.get("source_a") or "").strip()
        source_b=str(m.get("source_b") or "").strip()
        if not (period_a and period_b and source_a.startswith("https://") and source_b.startswith("https://")):
            winner="Fuentes o períodos sin verificar"
        if period_a and period_b and period_a!=period_b:
            winner="No comparable: períodos distintos"
        if (va is None or vb is None) and comparable:
            winner="Dato insuficiente"
        unit=m.get("unit","")
        def fmt(v):
            if v is None:return "No disponible"
            if unit=="%":return f"{v:,.1f}%"
            if unit=="USD":return f"US$ {v:,.0f}"
            if unit=="x" or name in {"P/E","Forward P/E","PEG","EV/EBITDA"}:return f"{v:,.2f}x"
            return f"{v:,.2f}"
        desc=COMPARISON_HELP.get(key) if key else None
        if not desc:
            desc=m.get("description") or "Indicador adicional: interpretar según su definición y comparabilidad."
        if period_a or period_b:
            desc += f" · Período A: {period_a or 'no informado'}; período B: {period_b or 'no informado'}"
        if source_a.startswith("https://") and source_b.startswith("https://"):
            desc += " · Fuentes informadas para ambos activos (revisar antes de decidir)"
        rows.append({"Indicador":name,"Descripción":desc,a:fmt(va),b:fmt(vb),"Favorece":winner})
    st.subheader(f"Comparación de fundamentales · {a} vs {b}")
    if rows:
        # La explicación está en una línea secundaria bajo el nombre del indicador.
        html=['<div class="cmp-wrap"><table class="cmp-table"><thead><tr>',
              '<th>Indicador</th><th>'+__import__("html").escape(str(a))+'</th><th>'+
              __import__("html").escape(str(b))+'</th><th>Favorece</th></tr></thead><tbody>']
        from html import escape
        for r in rows:
            h=escape(str(r["Indicador"]))
            d=escape(str(r["Descripción"]))
            html.append(f'<tr><td><strong>{h}</strong><div class="cmp-desc">{d}</div></td>'
                        f'<td>{escape(str(r[a]))}</td><td>{escape(str(r[b]))}</td>'
                        f'<td>{escape(str(r["Favorece"]))}</td></tr>')
        html.append('</tbody></table></div>')
        st.markdown("""
        <style>
        .cmp-wrap{overflow-x:auto}
        .cmp-table{width:100%;border-collapse:collapse;font-size:.94rem}
        .cmp-table th,.cmp-table td{padding:12px;border-bottom:1px solid #344353;text-align:left}
        .cmp-table th{background:#182331}
        .cmp-desc{color:#92a4b7;font-size:.78rem;margin-top:3px;line-height:1.35}
        </style>""",unsafe_allow_html=True)
        st.markdown("".join(html),unsafe_allow_html=True)
        st.caption("«Favorece» solo se calcula cuando la comparación no está marcada como incompatible y existen cifras para ambas empresas. No es una recomendación ni un ganador global. Los múltiplos bajos pueden reflejar mayor riesgo; importan la calidad, el sector y la comparabilidad de las cifras.")
    else:
        st.info("No hay indicadores sectorialmente relevantes y verificables disponibles para esta comparación.")
    bullets=result.get("bullets",[])
    if isinstance(bullets,list) and bullets:
        st.markdown("### Resumen ejecutivo")
        for x in bullets[:6]:
            st.markdown(f"- {x}")
    if result.get("analysis"):
        st.markdown("### Desarrollo")
        st.markdown(result["analysis"])

st.title(page)
if page in ["Resumen","Diversificación","Evolución","Riesgo","Custodia","Posiciones"]:
    st.caption("Dashboard analítico de PMS Bersoch · navegación, filtros, drill-down y contexto compartido")

if page=="Resumen":
    render_global_context_banner()
    if not summary.get("reconciled",True):
        st.warning(
            "La cabecera resumida de Google Sheets no reconcilia con el detalle en este instante. "
            "El Dashboard está usando el detalle consolidado para evitar mostrar una caída ficticia; "
            "las variaciones quedan temporalmente ocultas."
        )
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
        st.subheader("Composición por tipo")
        source=data["app_feed_v2"].copy()
        if not source.empty and {"Ticker","Tipo","Valor USD_num"}.issubset(source.columns):
            source=source[source["Ticker"].notna()].copy()
            # Criterio económico: fondos y oro clasificados como ETF; FUT suma en Cripto.
            kinds=source["Tipo"].fillna("").astype(str).str.strip().str.lower()
            tickers=source["Ticker"].fillna("").astype(str).str.upper()
            source["Grupo"]=kinds.map({
                "cedear":"Cedear","acción ar":"Acción AR","accion ar":"Acción AR",
                "etf":"ETF","bono ar":"Soberanos","cripto":"Cripto","derivado":"Cripto"
            })
            source.loc[tickers.eq("FUT"),"Grupo"]="Cripto"
            source.loc[kinds.str.contains("fondo|fci|mutual|oro|gold",regex=True)|tickers.eq("GLD"),"Grupo"]="ETF"
            order=["Cedear","Acción AR","ETF","Cripto","Soberanos"]
            unknown=source.loc[source["Grupo"].isna() & ~tickers.eq("CASH")]
            if not unknown.empty:
                st.caption("Existen activos sin tipo clasificado; revisar su clasificación.")
            chart=source[source["Grupo"].isin(order)].groupby("Grupo",as_index=False)["Valor USD_num"].sum()
            total=float(source["Valor USD_num"].sum())
            chart["Peso"]=chart["Valor USD_num"]/total*100 if total else 0
            chart["Etiqueta"]=chart["Peso"].map(lambda x:f"{x:.1f}%".replace(".",","))
            chart=chart.sort_values("Peso",ascending=True)
            fig=px.bar(chart,x="Peso",y="Grupo",orientation="h",text="Etiqueta",
                       category_orders={"Grupo":chart["Grupo"].tolist()},
                       labels={"Peso":"% del patrimonio","Grupo":""},
                       color_discrete_sequence=["#598eb8"])
            style_bar(fig)
            fig.update_traces(textposition="outside",cliponaxis=False,width=0.42)
            fig.update_layout(height=260,margin=dict(l=10,r=40,t=10,b=10),showlegend=False,
                              xaxis_ticksuffix="%",yaxis_title=None)
            st.plotly_chart(fig,width='stretch')
            st.caption("Peso sobre patrimonio total; el efectivo se incluye en el total, pero no se grafica.")
        else:
            st.info("No hay información para la composición por tipo.")
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
            colored_variation(m_show),
            hide_index=True,width='stretch',
            column_config={
                "Valor USD_num":st.column_config.TextColumn("Valor USD"),
                "Peso_num":st.column_config.NumberColumn("Peso",format="%.1f%%"),
                "Variación_num":st.column_config.NumberColumn("Variación",format="%.1f%%"),
                "Nombre":st.column_config.TextColumn("Nombre",width="medium"),
                "Estado dato":st.column_config.TextColumn("Estado",width="small"),
            }
        )

    app_df=data.get("app_feed_v2",pd.DataFrame())
    look_df=data.get("looker_feed_v2",pd.DataFrame())
    app_total=float(app_df["Valor USD_num"].sum()) if not app_df.empty and "Valor USD_num" in app_df.columns else 0.0
    look_total=float(look_df["Valor USD_num"].sum()) if not look_df.empty and "Valor USD_num" in look_df.columns else 0.0
    home_total=float(summary.get("home_total",0) or 0)
    diff=look_total-app_total

    st.subheader("Principales posiciones")
    st.caption("Seleccionar una fila lleva ese ticker al Asesor IA y a Comparar. No modifica ni filtra la cartera.")
    top_positions_table(12)

elif page=="Diversificación":
    render_global_context_banner()
    ex=data["dashboard_exposicion_v2"].copy()
    st.caption("EXPOSICIÓN PATRIMONIAL  ·  composición por región y sector  ·  barras proporcionales en USD")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### Distribución geográfica")
        r=ex[["Región","Valor USD_num","Peso_num"]].dropna(subset=["Región"]).sort_values("Valor USD_num",ascending=True)
        r["Etiqueta"]=r["Peso_num"].map(lambda v:f"{v*100:.1f}%".replace(".",","))
        fig=px.bar(
            r,x="Valor USD_num",y="Región",orientation="h",text="Etiqueta",
            labels={"Valor USD_num":"Valor USD"},
            color_discrete_sequence=["#79bff2"]
        )
        style_bar(fig)
        finish_executive_bar(fig)
        fig.update_traces(textposition="outside",cliponaxis=False,textfont_size=13,
                          customdata=r[["Región"]].to_numpy(),
                          hovertemplate="<b>Región: %{y}</b><br>Monto: US$ %{x:,.0f}<extra></extra>")
        fig.update_layout(yaxis_title=None,margin=dict(l=14,r=96,t=24,b=44),height=390)
        ev=st.plotly_chart(fig,width='stretch',on_select="rerun",selection_mode="points",key="region_chart")
        try:
            pts=ev.selection.points
            if pts:
                set_context("Región",pts[0].get("y"))
        except Exception: pass
    with c2:
        st.markdown("### Distribución sectorial")
        s=ex[["Sector","Sector Valor USD_num","Sector Peso_num"]].dropna(subset=["Sector"]).sort_values("Sector Valor USD_num",ascending=True)
        s["Etiqueta"]=s["Sector Peso_num"].map(lambda v:f"{v*100:.1f}%".replace(".",","))
        fig=px.bar(
            s,x="Sector Valor USD_num",y="Sector",orientation="h",text="Etiqueta",
            labels={"Sector Valor USD_num":"Valor USD"},
            color_discrete_sequence=["#4f8fc7"]
        )
        style_bar(fig)
        finish_executive_bar(fig)
        fig.update_traces(textposition="outside",cliponaxis=False,textfont_size=13,
                          hovertemplate="<b>Sector: %{y}</b><br>Monto: US$ %{x:,.0f}<extra></extra>")
        fig.update_layout(yaxis_title=None,margin=dict(l=8,r=70,t=12,b=12))
        ev2=st.plotly_chart(fig,width='stretch',on_select="rerun",selection_mode="points",key="sector_chart")
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
        detail_show=detail.sort_values("Valor USD_num",ascending=False)[["Ticker","Nombre","Custodio","Cuenta","Tipo","Región directa","Sector directo","Valor USD_num","Peso cartera_num"]].copy()
        detail_show["Peso cartera_num"]=pct_points(detail_show["Peso cartera_num"])
        st.dataframe(
            detail_show,
            hide_index=True,width='stretch',
            column_config={
                "Valor USD_num":st.column_config.TextColumn("Valor USD"),
                "Peso cartera_num":st.column_config.NumberColumn("Peso cartera",format="%.1f%%"),
            }
        )


    if not detail.empty and st.session_state.get("analysis_context",{}).get("value"):
        _context_tickers=sorted(detail["Ticker"].dropna().astype(str).unique().tolist())
        if _context_tickers:
            _context_ticker=st.selectbox("Analizar activo de esta exposición",_context_tickers,key="bersoch_exposure_focus")
            if st.button("Abrir en Asesor IA",key="bersoch_exposure_to_ai"):
                st.session_state["active_ticker"]=_context_ticker
                st.session_state["force_page"]="Asesor IA"
                st.rerun()

    total_port = float(summary["total"]) if pd.notna(summary.get("total")) else 0.0
    crypto_port = float(summary["crypto"]) if pd.notna(summary.get("crypto")) else 0.0
    conventional_port = max(total_port - crypto_port, 0.0)

    app_positions=data.get("app_feed_v2",pd.DataFrame()).copy()
    if not app_positions.empty and "Tipo" in app_positions.columns and "Valor USD_num" in app_positions.columns:
        etf_port=float(app_positions.loc[
            app_positions["Tipo"].astype(str).str.upper().eq("ETF"),
            "Valor USD_num"
        ].sum())
    else:
        etf_port=0.0
    non_etf_port=max(total_port-etf_port,0.0)

    d1,d2=st.columns(2)
    with d1:
        st.markdown("### Cripto vs cartera convencional")
        pie_df = pd.DataFrame({
            "Segmento":["Crypto","Cartera convencional"],
            "Valor USD":[crypto_port, conventional_port]
        })
        fig = px.pie(
            pie_df,names="Segmento",values="Valor USD",hole=0.52,color="Segmento",
            color_discrete_map={"Crypto":"#5d1f35","Cartera convencional":"#5b8ecb"},
        )
        fig.update_traces(
            textposition="inside",
            textfont_size=15,
            texttemplate="%{label}<br>US$ %{value:,.0f}<br>%{percent}",
            hovertemplate="<b>%{label}</b><br>Valor: US$ %{value:,.0f}<br>Peso: %{percent}<extra></extra>"
        )
        fig.update_layout(height=380,margin=dict(l=10,r=10,t=10,b=10),legend_title_text="",
                          uniformtext=dict(minsize=15,mode="show"))
        st.plotly_chart(fig,width='stretch')

    with d2:
        st.markdown("### ETFs principales")
        st.caption("ETFs directos de la cartera · ordenados por valor, de mayor a menor.")
        etf_rows=app_positions.loc[
            app_positions["Tipo"].astype(str).str.upper().eq("ETF")
        ].copy() if not app_positions.empty and "Tipo" in app_positions.columns else pd.DataFrame()
        if not etf_rows.empty:
            if "Peso cartera_num" not in etf_rows.columns:
                etf_rows["Peso cartera_num"]=etf_rows["Valor USD_num"]/total_port if total_port else 0.0
            etf_rows=etf_rows.groupby("Ticker",as_index=False).agg(
                {"Valor USD_num":"sum","Peso cartera_num":"sum"}
            ).sort_values("Valor USD_num",ascending=False).head(8)
            etf_rows["Texto"]=etf_rows.apply(
                lambda r:f'{r["Peso cartera_num"]*100:.1f}%'.replace(".",","),axis=1
            )
            order=etf_rows["Ticker"].tolist()
            etf_chart=etf_rows.sort_values("Valor USD_num",ascending=True)
            fig=px.bar(etf_chart,x="Valor USD_num",y="Ticker",orientation="h",text="Texto",
                       labels={"Valor USD_num":"Valor USD","Ticker":""},
                       color_discrete_sequence=["#528fbf"],
                       category_orders={"Ticker":order[::-1]})
            style_bar(fig)
            fig.update_yaxes(categoryorder="array",categoryarray=order[::-1])
            fig.update_traces(textposition="outside",cliponaxis=False,width=0.54,textfont_size=14,
                              hovertemplate="<b>ETF: %{y}</b><br>Monto: US$ %{x:,.0f}<extra></extra>")
            fig.update_yaxes(tickfont_size=14)
            fig.update_layout(height=max(260,52*len(etf_chart)+65),showlegend=False,
                              margin=dict(l=5,r=165,t=6,b=30),bargap=0.12)
            st.plotly_chart(fig,width="stretch")
        else:
            st.caption("No hay ETFs directos para mostrar.")

elif page=="Evolución":
    snaps=data.get("snapshot_series_v2",pd.DataFrame()).copy()
    if not snaps.empty and "Valor total USD_num" in snaps.columns:
        snaps["Fecha orden"]=pd.to_datetime(snaps["Fecha"],dayfirst=True,errors="coerce",format="mixed")
        snaps=snaps.dropna(subset=["Fecha orden"]).sort_values("Fecha orden").drop_duplicates(subset=["Fecha orden"],keep="last")
        snaps=snaps.loc[snaps["Valor total USD_num"]>0].copy()
        snaps["Cambio USD"]=snaps["Valor total USD_num"].diff()
        snaps["Cambio %"]=snaps["Valor total USD_num"].pct_change()*100
        if len(snaps)>1:
            latest=snaps.iloc[-1]; prev=snaps.iloc[-2]
            st.subheader("Cambio entre snapshots")
            x,y,z=st.columns(3)
            x.metric("Último patrimonio",fmt_usd(latest["Valor total USD_num"]))
            y.markdown(f'**Cambio USD**\n\n<span style="{signed_color(latest["Cambio USD"])};font-size:2rem;font-weight:600">{signed_number(latest["Cambio USD"])}</span>',unsafe_allow_html=True)
            z.markdown(f'**Cambio %**\n\n<span style="{signed_color(latest["Cambio %"])};font-size:2rem;font-weight:600">{signed_number(latest["Cambio %"],percentage=True)}</span>',unsafe_allow_html=True)
            st.caption(f'Del {prev["Fecha orden"].strftime("%d/%m/%Y")} al {latest["Fecha orden"].strftime("%d/%m/%Y")} · variación patrimonial sin ajustar por aportes/retiros; no es rentabilidad.')
        snap_show=snaps[["Fecha","Fecha orden","Valor total USD_num","Cambio USD","Cambio %"]].tail(20).sort_values("Fecha orden",ascending=False).copy()
        snap_show["Patrimonio USD"]=snap_show["Valor total USD_num"].map(fmt_usd)
        raw_usd=snap_show["Cambio USD"].copy()
        raw_pct=snap_show["Cambio %"].copy()
        snap_show["Fecha"]=snap_show["Fecha orden"].dt.strftime("%d/%m/%Y")
        snap_show["Cambio USD"]=raw_usd.map(signed_number)
        snap_show["Cambio %"]=raw_pct.map(lambda v:signed_number(v,percentage=True))
        snapshot_style=snap_show[["Fecha","Patrimonio USD","Cambio USD","Cambio %"]].style.apply(lambda _: [signed_color(x) for x in raw_usd],subset=["Cambio USD"],axis=0).apply(lambda _: [signed_color(x) for x in raw_pct],subset=["Cambio %"],axis=0)
        st.dataframe(snapshot_style,hide_index=True,width="stretch")
    # Serie cronológica completa de cierres observados, sin inferir días intermedios.
    if not snaps.empty and "Fecha orden" in snaps.columns:
        hist=snaps[["Fecha orden","Valor total USD_num"]].copy()
    else:
        evo=data["dashboard_evolucion_v2"].copy()
        evo["Fecha orden"]=pd.to_datetime(evo["Fecha"],dayfirst=True,errors="coerce",format="mixed")
        hist=evo[["Fecha orden","Valor total USD_num"]].dropna(subset=["Fecha orden"])
    hist=hist.loc[hist["Valor total USD_num"].gt(0)].sort_values("Fecha orden")
    hist=hist.drop_duplicates("Fecha orden",keep="last")
    from pms_evolution import observed_window
    _period=st.segmented_control("Período observado",["1M","3M","6M","1A","3A","5A","Todo"],default="Todo",key="bersoch_evolution_period")
    _all_observations=len(hist)
    hist=observed_window(hist,"Fecha orden",_period or "Todo")
    st.caption(f"Cobertura: {len(hist)} de {_all_observations} cierres observados. Las fechas sin datos no se completan.")
    if len(hist)>1:
        _first,_end=hist.iloc[0],hist.iloc[-1]
        _difference=float(_end["Valor total USD_num"]-_first["Valor total USD_num"])
        st.metric("Cambio patrimonial entre extremos observados",fmt_usd(_difference))
        st.caption("Desde "+_first["Fecha orden"].strftime("%d/%m/%Y")+" hasta "+_end["Fecha orden"].strftime("%d/%m/%Y")+" · incluye aportes/retiros no identificados; no es rentabilidad.")
    if hist.empty:
        st.info("No hay cierres observados para el período seleccionado.")
    else:
        fig=px.line(hist,x="Fecha orden",y="Valor total USD_num",markers=True,
                    labels={"Fecha orden":"Fecha","Valor total USD_num":"Patrimonio USD"})
        fig.update_layout(height=420,margin=dict(l=10,r=10,t=15,b=15))
        fig.update_yaxes(autorange=True, rangemode="tozero")
        st.plotly_chart(fig,width="stretch")
    st.caption(f'{len(hist)} cierres reales en el período seleccionado · sin interpolar fechas faltantes. La variación patrimonial no equivale a rentabilidad.')
    st.subheader("Reconstrucción histórica 2024–2026")
    st.caption("Los movimientos históricos no equivalen a valuaciones mensuales. Para graficar por tipo se requieren cantidades conciliadas y precios verificables de cada cierre.")
    try:
        _audit_ops=pd.read_csv(
            f"https://docs.google.com/spreadsheets/d/{PORTFOLIO['sheet_id']}/gviz/tq?tqx=out:csv&sheet=operaciones_normalizadas"
        )
        _audit_prices=pd.read_csv(
            f"https://docs.google.com/spreadsheets/d/{PORTFOLIO['sheet_id']}/gviz/tq?tqx=out:csv&sheet=historial_precios"
        )
        _ops_dates=pd.to_datetime(_audit_ops.get("Fecha",pd.Series(dtype=str)),errors="coerce",dayfirst=True)
        _price_dates=pd.to_datetime(_audit_prices.get("Fecha",pd.Series(dtype=str)),errors="coerce",dayfirst=True)
        _ops_months=set(_ops_dates.dropna().dt.to_period("M").astype(str))
        _priced_months=set(_price_dates.dropna().dt.to_period("M").astype(str))
        _history_months=sorted(_ops_months)
        if _history_months:
            _coverage=pd.DataFrame({
                "Mes":_history_months,
                "Operaciones":_audit_ops.assign(_mes=_ops_dates.dt.to_period("M").astype(str)).groupby("_mes").size().reindex(_history_months,fill_value=0).values,
                "Precios registrados": ["Sí" if m in _priced_months else "No" for m in _history_months],
            })
            st.dataframe(_coverage,hide_index=True,width="stretch")
            st.caption("Presencia de precios no implica cobertura completa de todos los instrumentos. Esta tabla es de auditoría; los meses sin valuación íntegra no se grafican como patrimonio.")
    except (OSError,ValueError,KeyError,TypeError) as _audit_error:
        st.info("La auditoría mensual de operaciones y cotizaciones no está disponible en este momento. No se generan estimaciones.")
    st.subheader("Cierre mensual observado")
    st.caption("Última observación disponible de cada mes, no necesariamente del último día hábil. No se reconstruyen meses sin valuación.")
    _monthly_source=snaps[["Fecha orden","Valor total USD_num"]].copy() if not snaps.empty and "Fecha orden" in snaps.columns else hist.copy()
    if not _monthly_source.empty:
        _monthly_source=_monthly_source.dropna(subset=["Fecha orden"]).sort_values("Fecha orden")
        _monthly_source=_monthly_source.loc[_monthly_source["Valor total USD_num"].gt(0)].copy()
        _monthly_source["Mes"]=_monthly_source["Fecha orden"].dt.to_period("M").astype(str)
        _monthly=_monthly_source.groupby("Mes",as_index=False).tail(1).copy()
        _monthly=_monthly.sort_values("Fecha orden")
        _monthly["Mes etiqueta"]=_monthly["Fecha orden"].dt.strftime("%m/%Y")
        _monthly_chart=px.bar(_monthly,x="Mes etiqueta",y="Valor total USD_num",
                              labels={"Mes etiqueta":"Mes observado","Valor total USD_num":"Patrimonio USD"},
                              hover_data={"Fecha orden":True})
        _monthly_chart.update_layout(height=340,margin=dict(l=10,r=10,t=15,b=35),showlegend=False)
        _monthly_chart.update_yaxes(rangemode="tozero")
        st.plotly_chart(_monthly_chart,width="stretch")
        st.caption(f"{len(_monthly)} meses con valuación observada. La serie histórica desde 2024 requiere precios y tenencias conciliados para cada cierre.")
    else:
        st.info("Todavía no hay observaciones mensuales verificables.")
    st.subheader("Variación diaria · 15 principales activos")
    app=data["app_feed_v2"].copy()
    top=app[app["Ticker"].notna()].sort_values("Valor USD_num",ascending=False).head(15).copy()
    top["Cotización"]=top.apply(quote_text,axis=1)
    evo_show=top[["Ticker","Nombre","Valor USD_num","Peso_num","Cotización","Variación_num","Estado dato"]].copy()
    evo_show["Peso_num"]=pct_points(evo_show["Peso_num"])
    evo_show["Variación_num"]=pct_points(evo_show["Variación_num"])
    st.dataframe(
        colored_variation(evo_show),hide_index=True,width='stretch',
        column_config={
            "Valor USD_num":st.column_config.TextColumn("Valor USD"),
            "Peso_num":st.column_config.NumberColumn("Peso",format="%.1f%%"),
            "Variación_num":st.column_config.NumberColumn("Variación",format="%.1f%%"),
        }
    )
    if not top.empty:
        _ev_ticker=st.selectbox("Abrir un activo del Top 15",top["Ticker"].astype(str).tolist(),key="bersoch_evolution_ticker")
        if st.button("Analizar ticker seleccionado",key="bersoch_evolution_to_ai"):
            st.session_state["active_ticker"]=_ev_ticker
            st.session_state["force_page"]="Asesor IA"
            st.rerun()

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
            stress["_impact_order"]=pd.to_numeric(stress[impact_usd_col],errors="coerce").abs()
            stress=stress.sort_values("_impact_order",ascending=True)
            fig=px.bar(
                stress,x=impact_usd_col,y="Métrica",orientation="h",
                labels={impact_usd_col:"Impacto USD"},
                color_discrete_sequence=["#d06a74"]
            )
            style_bar(fig)
            st.plotly_chart(fig,width='stretch')
        elif impact_pct_col:
            tmp=stress.copy()
            if "%" in impact_pct_col and not impact_pct_col.endswith("_num"):
                tmp["_impact_pct"]=tmp[impact_pct_col].map(local_num)
            else:
                tmp["_impact_pct"]=pd.to_numeric(tmp[impact_pct_col],errors="coerce")*100
            tmp["_impact_order"]=pd.to_numeric(tmp["_impact_pct"],errors="coerce").abs()
            tmp=tmp.sort_values("_impact_order",ascending=True)
            fig=px.bar(
                tmp,x="_impact_pct",y="Métrica",orientation="h",
                labels={"_impact_pct":"Impacto cartera (%)"},
                color_discrete_sequence=["#d06a74"]
            )
            style_bar(fig)
            st.plotly_chart(fig,width='stretch')
        else:
            st.info("Stress test disponible, pero la fuente no expone una columna de impacto graficable.")
    pending=risk[risk["Estado"].eq("HISTORIAL INSUFICIENTE")]
    if not pending.empty:
        st.subheader("Métricas aún no maduras")
        st.dataframe(pending[["Métrica","Estado","Interpretación"]],hide_index=True,width='stretch')

    st.subheader("Concentración por posición")
    top_positions_table(15)

    st.subheader("Solapamiento relevante en ETF · principales componentes")
    st.caption("Estimación parcial solo con participaciones principales fechadas y documentadas; el resto del ETF queda expresamente sin desagregar.")
    from pathlib import Path as _Path
    from pms_etf_overlap import approximate_etf_overlap
    _etf_snapshot=_Path(__file__).with_name("etf_top_holdings.csv")
    if _etf_snapshot.exists():
        _etf_weights=pd.read_csv(_etf_snapshot)
        if not _etf_weights.empty:
            try:
                _overlap,_coverage=approximate_etf_overlap(data.get("app_feed_v2",pd.DataFrame()),_etf_weights,max_names=10)
                if not _overlap.empty:
                    _overlap_show=_overlap.head(20).copy()
                    for _column in ("Directo USD","ETF parcial USD","Total identificado USD"):
                        _overlap_show[_column]=_overlap_show[_column].map(fmt_usd)
                    st.dataframe(_overlap_show,hide_index=True,width='stretch')
                if not _coverage.empty:
                    _remaining=float(_coverage["Valor sin desagregar USD"].sum())
                    st.caption("ETF no desagregados dentro de la selección: "+fmt_usd(_remaining)+" · no se asignan artificialmente a ningún emisor o sector.")
            except (ValueError,KeyError,TypeError) as _exc:
                st.warning("Composición ETF no válida: "+str(_exc))
    else:
        st.caption("Se incorporarán las principales participaciones con fuente y fecha al revisar el benchmark; no se estiman pesos sin respaldo.")
elif page=="Custodia":
    cash_df=data.get("custodia_cash_v2",pd.DataFrame()).copy()  # Sólo conciliación interna, no mostrar efectivo.
    summ=data["app_custodia_resumen_v2"].copy()
    detail=data["app_custodia_detalle_v2"].copy()
    # Control interno de conciliación. Vista visible: únicamente títulos y otros activos invertidos.
    detail_visible=detail[detail["Ticker"].astype(str).str.upper()!="CASH"].copy()
    # Control de integridad de solo lectura: nunca incorpora CASH como activo adicional.
    position_total=float(data["app_feed_v2"]["Valor USD_num"].sum())
    custody_total=float(summ["Valor USD_num"].sum())
    difference=position_total-custody_total
    # Diferencias de pocos centavos son esperables por redondeo de custodia.
    position_count=len(data["app_feed_v2"].dropna(subset=["Ticker"]))
    cust_count=detail["Ticker"].dropna().astype(str).nunique()
    # Conciliación por ticker: detecta diferencias compensadas que un total global ocultaría.
    by_position=data["app_feed_v2"].dropna(subset=["Ticker"]).groupby("Ticker")["Valor USD_num"].sum()
    by_custody=detail.dropna(subset=["Ticker"]).groupby("Ticker")["Valor USD_num"].sum()
    ticker_delta=by_position.sub(by_custody,fill_value=0.0)
    ticker_issues=ticker_delta[ticker_delta.abs()>0.10]
    cash_position=float(data["app_feed_v2"].loc[data["app_feed_v2"]["Ticker"].astype(str).str.upper()=="CASH","Valor USD_num"].sum())
    cash_cut=0.0
    if not cash_df.empty and "Valor USD al corte" in cash_df.columns:
        cash_cut=sum(local_num(v) for v in cash_df["Valor USD al corte"] if pd.notna(v)) * 1
    cash_gap=abs(cash_position-cash_cut)/cash_cut if cash_cut>0 else float("inf")
    # Controles internos; sin exponer umbrales ni auditorias en el dashboard.
    st.session_state["_custody_integrity_ok"]=bool(abs(difference)<=max(0.10,position_total*0.000001) and position_count==cust_count and ticker_issues.empty)
    st.session_state["_cash_integrity_ok"]=bool(cash_cut>0 and cash_gap<=0.02)
    st.caption("CUSTODIA  ·  concentración por intermediario y detalle por cuenta")
    cust_options=["TODOS"]+sorted(detail_visible["Custodio"].dropna().astype(str).unique().tolist())
    cust=st.selectbox("Custodio",cust_options,index=0)

    # Dos universos explícitos: patrimonio custodio incluye efectivo;
    # la tabla navegable presenta solo activos invertidos.
    if cust=="TODOS":
        st.session_state["analysis_context"]={"dimension":"","value":""}
        custody_scope=detail.copy()
        rows=detail_visible.copy().sort_values("Valor USD_num",ascending=False)
    else:
        st.session_state["analysis_context"]={"dimension":"Custodio","value":cust}
        custody_scope=detail[detail["Custodio"]==cust].copy()
        rows=detail_visible[detail_visible["Custodio"]==cust].copy().sort_values("Valor USD_num",ascending=False)
    total_val=float(custody_scope["Valor USD_num"].sum())
    invested_val=float(rows["Valor USD_num"].sum())
    total_accounts=int(custody_scope["Cuenta"].nunique())
    c1,c2,c3=st.columns(3)
    c1.metric("Patrimonio bajo custodia",fmt_usd(total_val))
    c2.metric("Peso en cartera",fmt_pct(total_val/position_total if position_total else 0))
    c3.metric("Cuentas",total_accounts)
    st.caption(
        f"Patrimonio invertido: {fmt_usd(invested_val)} ({fmt_pct(invested_val/position_total if position_total else 0)} de cartera)"
        " · CASH incluido en custodia y patrimonio, excluido del detalle de títulos."
    )

    # Navegación progresiva: custodio → cuenta → ticker; nunca cambia el patrimonio consolidado.
    accounts=sorted(rows["Cuenta"].dropna().astype(str).unique().tolist())
    account=st.selectbox("Cuenta",["Todas las cuentas"]+accounts,key=f"custody_account_drill_{cust}")
    if account!="Todas las cuentas":
        rows=rows[rows["Cuenta"].astype(str)==account].copy()
    tickers=sorted(rows["Ticker"].dropna().astype(str).unique().tolist())
    ticker=st.selectbox("Activo",["Todos los activos"]+tickers,key=f"custody_ticker_drill_{cust}_{account}")
    if ticker!="Todos los activos":
        rows=rows[rows["Ticker"].astype(str)==ticker].copy()
    # Los filtros de cuenta y activo definen el universo patrimonial seleccionado.
    # CASH solo se excluye de la tabla de títulos, no del denominador ni del KPI.
    selected_scope=custody_scope.copy()
    if account!="Todas las cuentas":
        selected_scope=selected_scope[selected_scope["Cuenta"].astype(str)==account]
    if ticker!="Todos los activos":
        selected_scope=selected_scope[selected_scope["Ticker"].astype(str)==ticker]
    selected_value=float(selected_scope["Valor USD_num"].sum())
    selected_invested=float(rows["Valor USD_num"].sum())
    selected_weight=selected_value/position_total if position_total else 0.0
    st.caption("Patrimonio seleccionado (sin modificar el patrimonio global)")
    v1,v2,v3=st.columns(3)
    v1.metric("Valor seleccionado",fmt_usd(selected_value))
    v2.metric("Peso en cartera",fmt_pct(selected_weight))
    v3.metric("Títulos visibles",len(rows))
    if ticker=="Todos los activos":
        st.caption(f"Invertido visible: {fmt_usd(selected_invested)} · CASH incluido en patrimonio seleccionado, no listado como título.")
    if rows.empty:
        st.info("No hay posiciones con estos filtros.")
    if cust=="TODOS":
        st.subheader("Distribución por custodio")
        # Agrupar patrimonio completo (incluye CASH) por custodio y cuenta. Sólo Criteria se
        # desglosa visualmente por cuenta; los demás quedan como una barra.
        chart_data=custody_scope.dropna(subset=["Custodio"]).copy()
        chart_data["Custodio"]=chart_data["Custodio"].astype(str)
        chart_data["Cuenta"]=chart_data["Cuenta"].fillna("Sin cuenta").astype(str)
        chart_data["Grupo"]=chart_data.apply(
            lambda r: r["Cuenta"] if r["Custodio"].strip().upper()=="CRITERIA" else r["Custodio"],axis=1
        )
        chart_data=chart_data.groupby(["Custodio","Grupo"],as_index=False)["Valor USD_num"].sum()
        cust_totals=chart_data.groupby("Custodio")["Valor USD_num"].sum().sort_values(ascending=False)
        if not chart_data.empty:
            # Categorías mayores arriba. Criteria 4666/4704 tienen colores separados.
            fig=px.bar(
                chart_data,x="Valor USD_num",y="Custodio",color="Grupo",orientation="h",
                category_orders={"Custodio":cust_totals.index.tolist()[::-1]},
                labels={"Valor USD_num":"Valor USD","Grupo":"Cuenta / custodio"},
                hover_data={"Custodio":True,"Grupo":True,"Valor USD_num":":,.0f"},
                color_discrete_map={g:("#CDD2D9" if str(g).upper().endswith(("4666","1234")) else "#747D89") if str(c).strip().upper()=="CRITERIA" else custodian_color(c) for c,g in chart_data[["Custodio","Grupo"]].itertuples(index=False,name=None)}
            )
            style_bar(fig)
            finish_executive_bar(fig,stacked=True)
            fig.update_yaxes(categoryorder="array",categoryarray=cust_totals.index.tolist()[::-1])
            fig.update_layout(barmode="stack",height=max(300,65*len(cust_totals)+100),
                margin=dict(l=15,r=34,t=24,b=115),legend_title_text="")
            st.plotly_chart(fig,width='stretch')
        else:
            st.info("No hay valores por custodio para graficar.")
    else:
        st.subheader(f"Principales posiciones · {cust}")
        chart_rows=rows.head(15).sort_values("Valor USD_num",ascending=True)
        if chart_rows.empty:
            st.info("Sin activos para mostrar con estos filtros.")
        else:
            fig=px.bar(
                chart_rows,x="Valor USD_num",y="Ticker",color="Cuenta",orientation="h",
                labels={"Valor USD_num":"Valor USD"}
            )
            style_bar(fig)
            finish_executive_bar(fig,stacked=True)
            st.plotly_chart(fig,width='stretch')
    rows_show=rows[["Cuenta","Ticker","Nombre","Tipo","Cantidad_num","Valor USD_num","Peso custodio_num"]].copy()
    rows_show["Cantidad_num"]=rows_show["Cantidad_num"].map(lambda x:fmt_num(x,0) if float(x).is_integer() else fmt_num(x,4))
    rows_show["Peso custodio_num"]=pct_points(rows_show["Peso custodio_num"])
    st.dataframe(
        table_money(rows_show),hide_index=True,width='stretch',
        column_config={
            "Valor USD_num":st.column_config.TextColumn("Valor USD"),
            "Cantidad_num":st.column_config.TextColumn("Unidades"),
            "Peso custodio_num":st.column_config.NumberColumn("Peso custodio",format="%.1f%%"),
        }
    )

elif page=="Posiciones":
    with st.expander("Bonos · Data912 (referencia experimental, no afecta patrimonio)",expanded=False):
        st.caption("Fuente pública sin credenciales. El precio crudo NO indica moneda, unidad nominal ni fecha de mercado verificadas. No se utiliza en las valuaciones.")
        if st.button("Consultar Data912",key="bond_watchlist_refresh"):
            try:
                from bond_watchlist import read_bond_watchlist
                with st.spinner("Consultando precios de referencia…"):
                    st.session_state["bond_watchlist_result"]=read_bond_watchlist()
                st.session_state.pop("bond_watchlist_error",None)
            except Exception as exc:
                st.session_state.pop("bond_watchlist_result",None)
                st.session_state["bond_watchlist_error"]="No se pudo consultar la fuente pública: "+str(exc)[:160]
        if st.session_state.get("bond_watchlist_error"):
            st.warning(st.session_state["bond_watchlist_error"])
        if st.session_state.get("bond_watchlist_result"):
            st.dataframe(pd.DataFrame(st.session_state["bond_watchlist_result"]),hide_index=True,width="stretch")
            st.caption("Solo consulta informativa. No equivale a una actualización del PMS.")
    st.caption("Filtros exclusivos de esta tabla. No modifican el patrimonio general ni la actualización.")
    f1,f2,f3=st.columns(3)
    with f1:
        sel_cust=st.selectbox("Custodio",["Todos"]+sorted(positions["Custodio"].dropna().astype(str).unique().tolist()),key="pos_custodio")
    with f2:
        sel_tipo=st.selectbox("Tipo",["Todos"]+sorted(positions["Tipo"].dropna().astype(str).unique().tolist()),key="pos_tipo")
    with f3:
        sel_region=st.selectbox("Región",["Todas"]+sorted(positions["Región directa"].dropna().astype(str).unique().tolist()),key="pos_region")
    filtered=positions.copy()
    if sel_cust!="Todos": filtered=filtered[filtered["Custodio"]==sel_cust]
    if sel_tipo!="Todos": filtered=filtered[filtered["Tipo"]==sel_tipo]
    if sel_region!="Todas": filtered=filtered[filtered["Región directa"]==sel_region]
    filtered=apply_analysis_context(filtered)
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
            "Cuenta":lambda s:", ".join(sorted(set(str(x) for x in s if pd.notna(x)))),
            "Cantidad_num":"sum"
        })
        total_base=float(data.get("app_feed_v2",pd.DataFrame()).get("Valor USD_num",pd.Series(dtype=float)).sum())
        agg["Peso cartera_num"]=agg["Valor USD_num"]/total_base if total_base else 0.0
        view=agg.sort_values("Valor USD_num",ascending=False)
    else:
        view=view.sort_values("Valor USD_num",ascending=False)

    st.caption(f"{len(view)} filas · {fmt_usd(view['Valor USD_num'].sum())}")
    view_show=view[["Ticker","Nombre","Cuenta","Tipo","Cantidad_num","Valor USD_num","Peso cartera_num","Variación_num","Estado dato"]].copy()
    view_show["Cantidad_num"]=view_show["Cantidad_num"].map(lambda x:fmt_num(x,0) if float(x).is_integer() else fmt_num(x,4))
    view_show["Peso cartera_num"]=pct_points(view_show["Peso cartera_num"])
    view_show["Variación_num"]=pct_points(view_show["Variación_num"])
    pos_event=st.dataframe(
        colored_variation(view_show),
        hide_index=True,width='stretch',height=700,
        on_select="rerun",selection_mode="single-row",key="positions_table",
        column_config={
            "Valor USD_num":st.column_config.TextColumn("Valor USD"),
            "Cantidad_num":st.column_config.TextColumn("Unidades"),
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


elif page=="Comparar":
    st.subheader("Comparación patrimonial")
    st.caption("Valores y pesos de dos instrumentos de la cartera Bersoch; sin mezclar fuentes con DEMO.")
    _cmp_positions=data.get("app_feed_v2",pd.DataFrame()).copy()
    if {"Ticker","Valor USD_num"}.issubset(_cmp_positions.columns):
        _cmp_options=sorted(set(_cmp_positions["Ticker"].dropna().astype(str))-{"CASH"})
        if len(_cmp_options)>1:
            _cmp_a,_cmp_b=st.columns(2)
            _cmp_left=_cmp_a.selectbox("Posición A",_cmp_options,key="bersoch_cmp_port_a")
            _cmp_right=_cmp_b.selectbox("Posición B",_cmp_options,index=1,key="bersoch_cmp_port_b")
            if _cmp_left==_cmp_right:
                st.warning("Seleccioná instrumentos diferentes.")
            else:
                from pms_compare import compare_portfolio_positions
                _cmp_total=float(_cmp_positions["Valor USD_num"].sum())
                _cmp_result=compare_portfolio_positions(_cmp_positions,_cmp_left,_cmp_right,_cmp_total)
                _cmp_result["Valor USD"]=_cmp_result["Valor USD"].map(fmt_usd)
                _cmp_result["Peso cartera"]=_cmp_result["Peso cartera"].map(fmt_pct)
                st.dataframe(_cmp_result[["Ticker","Tipo","Valor USD","Peso cartera"]],hide_index=True,width="stretch")
        else:
            st.info("Se necesitan al menos dos posiciones para comparar.")
    st.divider()
    st.subheader("Comparar de empresas")
    st.caption("Herramienta analítica independiente del chat. Usa datos externos actuales y contexto de PMS Bersoch.")
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
    st.caption("Impacto estimado sobre la cartera actual. No ejecuta operaciones; no incluye comisiones ni deslizamiento.")
    render_active_context()
    holdings=data.get("app_feed_v2",pd.DataFrame()).copy()
    if holdings.empty:
        st.info("No se dispone de la cartera para simular.")
    else:
        tickers=sorted(t for t in holdings["Ticker"].dropna().astype(str).unique() if t!="CASH")
        if not tickers:
            st.info("No hay posiciones distintas de CASH para simular.")
            st.stop()
        active=st.session_state.get("active_ticker","")
        idx=tickers.index(active) if active in tickers else 0
        a,b,c=st.columns([1,1,1.1])
        ticker=a.selectbox("Activo",tickers,index=idx,key="sim_ticker")
        operation=b.selectbox("Operación",["Comprar","Vender"],key="sim_op")
        amount=c.number_input("Monto USD",min_value=0.0,step=100.0,key="sim_amount")
        source_ticker=None
        cash_amount=0.0
        if operation=="Comprar":
            funding_mode=st.selectbox("¿De dónde salen los fondos?",
                ["CASH","Venta de otro activo","CASH + venta de activo","Aporte externo"],
                help="La venta es una operación simulada simultánea: los fondos obtenidos financian la compra sin cambiar el patrimonio.")
            if funding_mode in ("Venta de otro activo","CASH + venta de activo"):
                options=[t for t in tickers if t!=ticker]
                source_ticker=st.selectbox("Activo a vender para financiar",options)
                if funding_mode=="CASH + venta de activo":
                    max_cash=min(float(holdings.loc[holdings["Ticker"]=="CASH","Valor USD_num"].sum()),float(amount))
                    cash_amount=st.number_input("Usar de CASH (USD)",min_value=0.0,max_value=max(0.0,max_cash),value=0.0,step=100.0)
                    st.caption(f"Venta estimada de {source_ticker}: {fmt_usd(max(0.0,amount-cash_amount))}")
                else:
                    st.caption(f"Venta estimada de {source_ticker}: {fmt_usd(amount)}")
        else:
            funding_mode=st.selectbox("Destino de los fondos",["CASH","Retiro externo"],
                help="CASH conserva el patrimonio dentro de la cartera; retiro externo lo reduce.")

        if amount>0:
            sim=simulate_trade(ticker,operation,amount,funding_mode,source_ticker,cash_amount)
            if sim and sim.get("error"):
                st.error(sim["error"])
            elif sim:
                def sim_delta_usd(value):
                    return f"{'+' if value>0 else '-' if value<0 else ''}{fmt_usd(abs(value))}"
                with st.container(key="simulator_metrics"):
                    a,b,c=st.columns(3)
                    a.metric("Valor posición",fmt_usd(sim["value_after"]),
                             delta=sim_delta_usd(sim["value_after"]-sim["value_before"]))
                    b.metric("Peso posición",fmt_pct(sim["weight_after"]),
                             delta=f'{(sim["weight_after"]-sim["weight_before"])*100:+.2f} pp')
                    c.metric("CASH",fmt_usd(sim["cash_after"]),
                             delta=sim_delta_usd(sim["cash_after"]-sim["cash_before"]),
                             delta_color="off")
                    d,e=st.columns(2)
                    diff=sim["total_after"]-sim["total_before"]
                    d.metric("Patrimonio total",fmt_usd(sim["total_after"]),
                             delta=sim_delta_usd(diff),delta_color="off" if abs(diff)<0.005 else "normal")
                    e.metric("Top 5",fmt_pct(sim["top5_after"]),
                             delta=f'{(sim["top5_after"]-sim["top5_before"])*100:+.2f} pp',delta_color="off")
                st.markdown("#### Antes vs. después")
                rows=[
                    ("Activo "+ticker,sim["value_before"],sim["value_after"],"USD"),
                    ("CASH",sim["cash_before"],sim["cash_after"],"USD"),
                ]
                if sim.get("source_ticker"):
                    rows.append(("Activo "+str(sim["source_ticker"]),sim["source_before"],sim["source_after"],"USD"))
                rows.append(("Patrimonio",sim["total_before"],sim["total_after"],"USD"))
                table=pd.DataFrame([{"Concepto":label,"Antes":before,"Después":after,"Cambio":after-before}
                                    for label,before,after,unit in rows])
                # Importes enteros con separador de miles argentino; sin decimales.
                for column in ("Antes", "Después", "Cambio"):
                    table[column] = table[column].map(fmt_usd)
                st.dataframe(table, hide_index=True, width="stretch")
                x,y=st.columns(2)
                x.metric("Peso del activo · antes → después",
                    f"{fmt_pct(sim['weight_before'])} → {fmt_pct(sim['weight_after'])}")
                y.metric("Concentración Top 5 · antes → después",
                    f"{fmt_pct(sim['top5_before'])} → {fmt_pct(sim['top5_after'])}")
                st.caption("Los cambios en USD y los cambios de peso se muestran por separado para no mezclar escalas.")
                if st.button("Pedir lectura al Asesor IA",key="sim_to_ai"):
                    description=f"{operation.lower()} US$ {amount:,.0f} de {ticker} ({funding_mode})"
                    if sim.get("source_ticker"):
                        description+=f", financiado con venta de {sim['source_ticker']}"
                    st.session_state["force_page"]="Asesor IA"
                    st.session_state["pending_advisor_prompt"]=(
                        f"Analizá esta simulación: {description}. "
                        f"Peso del activo: {fmt_pct(sim['weight_before'])} → {fmt_pct(sim['weight_after'])}. "
                        f"Top 5: {fmt_pct(sim['top5_before'])} → {fmt_pct(sim['top5_after'])}. "
                        "Evaluá concentración, diversificación y riesgos frente a la cartera.")
                    st.rerun()

elif page=="Asesor IA":
    with st.expander("Análisis técnico · 5 años, EMA y RSI", expanded=True):
        st.caption("Indicadores diarios determinísticos sobre cierres ajustados. Fuente: Yahoo Finance (vía yfinance). Elegí el símbolo cotizado, por ejemplo AAPL o GGAL.BA; no se supone equivalencia automática con CEDEARs.")
        symbol_default=str(st.session_state.get("active_ticker","") or "").strip().upper()
        # Sincronizar sólo cuando la selección global cambió, preservando la edición manual.
        if st.session_state.get("_technical_last_active_ticker")!=symbol_default:
            if symbol_default:
                st.session_state["technical_symbol"]=symbol_default
            st.session_state["_technical_last_active_ticker"]=symbol_default
        technical_symbol=st.text_input("Símbolo histórico",value=symbol_default,key="technical_symbol")
        selected_window=st.radio("Ventana",["6M","1A","3A","5A"],index=3,horizontal=True,key="technical_window")
        @st.cache_data(ttl=3600,show_spinner=False)
        def _cached_technical_history(sym):
            from technical import fetch_history
            return fetch_history(sym)

        current_symbol=str(technical_symbol or "").strip().upper()
        loaded_symbol=str(st.session_state.get("technical_loaded_symbol","")).strip().upper()
        # Seleccionar otro símbolo dispara automáticamente una única consulta.
        # Cachear hasta una hora; cambiar la ventana sólo filtra localmente.
        retry=st.button("Actualizar historial",key="technical_load",help="Opcional: fuerza una nueva consulta del símbolo.")
        if retry and current_symbol:
            _cached_technical_history.clear()
        # Sincronizar también un cambio de versión/datos sin requerir interacción.
        if current_symbol and (current_symbol!=loaded_symbol or retry):
            st.session_state["technical_loaded_symbol"]=current_symbol
            st.session_state.pop("technical_data",None)
            st.session_state.pop("technical_snapshot",None)
            st.session_state.pop("technical_error",None)
            try:
                with st.spinner("Actualizando análisis técnico…"):
                    st.session_state["technical_data"]=_cached_technical_history(current_symbol)
            except Exception as exc:
                st.session_state["technical_error"]=str(exc)[:180]
        elif not current_symbol:
            st.session_state.pop("technical_data",None)
            st.session_state.pop("technical_snapshot",None)
            st.session_state["technical_loaded_symbol"]=""
        technical_data=st.session_state.get("technical_data")
        if st.session_state.get("technical_error"):
            st.warning("No se pudo obtener el historial: "+st.session_state["technical_error"])
        if technical_data is not None and not technical_data.empty:
            st.caption(f"Símbolo consultado: {st.session_state.get('technical_loaded_symbol','')} · cierres ajustados diarios · los indicadores no son señales automáticas de compra o venta.")
            days={"6M":183,"1A":365,"3A":1095,"5A":1827}[selected_window]
            cut=technical_data.index.max()-pd.Timedelta(days=days)
            shown=technical_data.loc[technical_data.index>=cut]
            figure=px.line(shown,y=["Close","EMA 21","EMA 50","EMA 200"],labels={"value":"Precio ajustado","index":"Fecha","variable":"Serie"})
            figure.update_layout(height=370,legend_title_text="")
            st.plotly_chart(figure,width="stretch")
            rsi_fig=px.line(shown,y="RSI 14",labels={"value":"RSI 14","index":"Fecha"})
            rsi_fig.add_hline(y=70,line_dash="dash",line_color="#df9c5a")
            rsi_fig.add_hline(y=30,line_dash="dash",line_color="#74b7aa")
            rsi_fig.update_yaxes(range=[0,100])
            rsi_fig.update_layout(height=380,showlegend=False)
            st.plotly_chart(rsi_fig,width="stretch")
            last=shown.iloc[-1]
            st.caption(f"Cierre ajustado: {last['Close']:.2f} · Distancia EMA 200: {(last['Close']/last['EMA 200']-1)*100:+.1f}% · RSI 14: {last['RSI 14']:.1f} · {shown.index.max():%d/%m/%Y}")
            # Contexto técnico verificable del símbolo consultado, no del CEDEAR por inferencia.
            def _technical_number(v):
                return round(float(v),4) if pd.notna(v) and float(v)>0 else None
            st.session_state["technical_snapshot"]={
                "symbol":st.session_state.get("technical_loaded_symbol",""),
                "source":"Yahoo Finance / yfinance",
                "as_of":str(shown.index.max().date()),
                "price_currency":"No verificada: depende del mercado del símbolo consultado",
                "instrument_match_to_portfolio":"No verificado: no equiparar CEDEAR con acción subyacente",
                "close_adjusted":_technical_number(last["Close"]),
                "ema21":_technical_number(last["EMA 21"]),
                "ema50":_technical_number(last["EMA 50"]),
                "ema200":_technical_number(last["EMA 200"]),
                "rsi14":round(float(last["RSI 14"]),2) if pd.notna(last["RSI 14"]) else None,
                "sample_closes":int(len(technical_data)),
                "scope":"Observación técnica descriptiva, sin predicción ni recomendación"
            }
            st.caption("Indicadores disponibles para el Asesor IA. El historial se actualiza al cambiar el símbolo; la ventana sólo modifica la visualización.")
    st.subheader("Asesor IA")
    st.caption("Conversación libre y análisis contextual. Comparar y Simulador también tienen páginas propias.")
    try:
        advisor_ready=bool(st.secrets.get("OPENAI_API_KEY",""))
        advisor_model=st.secrets.get("OPENAI_MODEL","gpt-5.6")
    except Exception:
        advisor_ready=False
        advisor_model="gpt-5.6"

    if not advisor_ready:
        st.warning("El Asesor IA todavía no está activado. El Dashboard y las herramientas determinísticas funcionan normalmente.")
        with st.expander("Cómo activar el Asesor IA"):
            st.markdown("""
1. En Streamlit Cloud abrí **Manage app → Settings → Secrets**.
2. Agregá:
```toml
OPENAI_API_KEY = "tu_clave"
OPENAI_MODEL = "gpt-5.6"
```
3. Guardá los Secrets y reiniciá la app.

La clave queda en Streamlit Secrets y no debe subirse a GitHub.
""")
    else:
        st.success(f"Asesor IA configurado · modelo: {advisor_model}")
        st.caption("Las consultas con fundamentales/noticias pueden consumir más API porque usan búsqueda web.")
        if st.button("Probar conexión IA",key="advisor_self_test"):
            with st.spinner("Probando conexión…"):
                test_answer=ask_advisor(
                    "Respondé solamente: CONEXIÓN OK. No uses búsqueda web para esta prueba.",
                    data,
                    filtered,
                    history=[],
                    selected_ticker=st.session_state.get("active_ticker",""),
                    analysis_context=st.session_state.get("analysis_context",{})
                )
            st.info(test_answer)
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
                answer=ask_advisor(user_prompt,data,filtered,st.session_state.messages[-8:],selected_ticker=st.session_state.get("active_ticker",""),analysis_context=st.session_state.get("analysis_context",{}),technical_snapshot=st.session_state.get("technical_snapshot"))
            st.markdown(answer)
        st.session_state.messages.append({"role":"assistant","content":answer})
