"""Formatos reutilizables de la interfaz. No modifican datos de cartera."""
import pandas as pd

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
    """Aspecto compartido: barras compactas, borde fino y fondo transparente."""
    fig.update_traces(marker_line_width=1.6, marker_line_color="rgba(231,240,250,0.52)", opacity=0.96)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#dce6f2", bargap=0.42, barcornerradius=5,
        margin=dict(l=8,r=46,t=12,b=12),
        legend_title_text=""
    )
    if horizontal:
        fig.update_yaxes(title_text=None, showgrid=False, categoryorder="total ascending")
        fig.update_xaxes(gridcolor="rgba(170,193,214,0.12)", zeroline=False)
    return fig

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
