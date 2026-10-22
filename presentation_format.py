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
