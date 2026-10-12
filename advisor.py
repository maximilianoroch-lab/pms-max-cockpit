
import os,json,pandas as pd
from openai import OpenAI
from portfolio_config import PORTFOLIO

SYSTEM_CONTEXT=f"""Sos el asesor analítico de {PORTFOLIO["display_name"]}. Contrastá decisiones con datos, reducí sesgos emocionales y marcá inconsistencias sin ser condescendiente.
Esta instancia es privada y aislada. No mezcles, infieras ni reutilices información de otras carteras o entidades.
Reglas de esta cartera:
- Moneda principal: {PORTFOLIO["base_currency"]}.
- Patrimonio principal sin Crypto; Crypto se informa separada.
- FUT se integra a Crypto en análisis.
- GLD: clase Oro, tipo ETF.
- MELI, VIST y GLOB: Global.
- YPF/YPFD y GGAL directos: Argentina.
- Sólo FUT, CASH, GALILEO y SCHROD requieren actualización manual.
- Fines de semana/feriados aceptan último valor válido.
- No uses TWR, XIRR ni Modified Dietz salvo pedido explícito.
- No trates volatilidad/drawdown/correlaciones como maduras si el PMS marca historial insuficiente.
Separá datos internos de información externa. Para fundamentales, noticias, valuaciones o hechos recientes usá búsqueda web. No inventes datos.
No decidas por el usuario: presentá evidencia, contradicciones, riesgos y escenarios."""

def build_action_prompt(action,p):
    m={
    "Analizar cartera":"Analizá mi cartera actual. Marcá concentración, exposiciones, inconsistencias y qué merece atención hoy.",
    "Analizar ticker":f"Analizá {p.get('ticker')} como activo y como parte de mi cartera. Incluí valuación, fundamentales, riesgos, catalizadores y contexto de posición.",
    "Comparar empresas":f"Compará {p.get('ticker1')} vs {p.get('ticker2')}: valuación, crecimiento, márgenes, balance, FCF, riesgos y encaje en mi cartera.",
    "Consultar fundamentales":f"Consultá fundamentales actuales de {p.get('ticker')}: valuación, P/E si aplica, crecimiento, márgenes, balance y FCF. Indicá fecha y fuentes.",
    "Consultar noticias":f"Buscá noticias recientes y relevantes sobre {p.get('ticker')}. Separá hechos de interpretación y explicá impacto potencial en mi tesis.",
    "Explicar movimiento":f"Explicá el movimiento reciente de {p.get('ticker')}. Buscá causas verificables y separá precio de fundamentales.",
    "Simular operación":f"Simulá el impacto de {p.get('operation','').lower()} US$ {p.get('amount',0):.0f} de {p.get('ticker')} sobre pesos, concentración y exposiciones. No ejecutes nada."}
    return m.get(action,"")

def compact(data,filtered,selected_ticker=""):
    app=data.get("app_feed_v2",pd.DataFrame()).copy();risk=data.get("dashboard_riesgo_v2",pd.DataFrame()).copy();expo=data.get("dashboard_exposicion_v2",pd.DataFrame()).copy()
    top=[]
    if not app.empty:
        cols=[c for c in ["Ticker","Nombre","Valor USD_num","Peso_num","Tipo","Clase","Región","Sector","Variación_num","Estado dato"] if c in app]
        top=app[app["Ticker"].notna()].sort_values("Valor USD_num",ascending=False).head(20)[cols].fillna("").to_dict("records")
    f=[]
    if filtered is not None and not filtered.empty:
        cols=[c for c in ["Ticker","Nombre","Custodio","Cuenta","Valor USD_num","Peso cartera_num","Clase","Tipo","Región directa","Sector directo","Variación_num","Estado dato"] if c in filtered]
        f=filtered.sort_values("Valor USD_num",ascending=False).head(40)[cols].fillna("").to_dict("records")
    selected={}
    if selected_ticker:
        aa=app[app["Ticker"].astype(str)==str(selected_ticker)] if not app.empty else pd.DataFrame()
        pp=filtered[filtered["Ticker"].astype(str)==str(selected_ticker)] if filtered is not None and not filtered.empty else pd.DataFrame()
        if not aa.empty:
            rr=aa.iloc[0]
            selected={
                "Ticker":selected_ticker,"Nombre":rr.get("Nombre",""),"Valor USD":rr.get("Valor USD_num",0),
                "Peso":rr.get("Peso_num",0),"Variación":rr.get("Variación_num",0),"Tipo":rr.get("Tipo",""),
                "Clase":rr.get("Clase",""),"Región":rr.get("Región",""),"Sector":rr.get("Sector",""),
                "Estado dato":rr.get("Estado dato","")
            }
        if not pp.empty:
            selected["Custodios"]=sorted(pp["Custodio"].dropna().astype(str).unique().tolist())
            selected["Cuentas"]=sorted(pp["Cuenta"].dropna().astype(str).unique().tolist())
    return {"top_positions":top,"filtered_positions":f,"selected_ticker":selected,"risk":risk.head(25).fillna("").to_dict("records"),"exposure":expo.head(20).fillna("").to_dict("records")}

def ask_advisor(user_prompt,data,filtered_positions,history=None,selected_ticker="",analysis_context=None):
    try:
        import streamlit as st
        api_key=st.secrets.get("OPENAI_API_KEY",os.getenv("OPENAI_API_KEY"))
        model=st.secrets.get("OPENAI_MODEL",os.getenv("OPENAI_MODEL","gpt-5.1"))
    except Exception:
        api_key=os.getenv("OPENAI_API_KEY");model=os.getenv("OPENAI_MODEL","gpt-5.1")
    if not api_key:
        return "El dashboard funciona, pero el Asesor IA todavía no tiene OPENAI_API_KEY configurada en los Secrets de Streamlit."
    ctx=compact(data,filtered_positions,selected_ticker)
    messages=[]
    for m in (history or [])[-6:]:
        if m.get("role") in ("user","assistant"):messages.append({"role":m["role"],"content":m["content"]})
    ctx["analysis_context"]=analysis_context or {}
    prompt="CONTEXTO ACTUAL DEL PMS:\n"+json.dumps(ctx,ensure_ascii=False,default=str)+"\n\nCONSULTA:\n"+user_prompt
    client=OpenAI(api_key=api_key)
    response=client.responses.create(model=model,instructions=SYSTEM_CONTEXT,input=messages+[{"role":"user","content":prompt}],tools=[{"type":"web_search"}])
    return response.output_text


def _extract_json(text):
    text=(text or "").strip()
    if text.startswith("```"):
        text=text.split("\n",1)[1] if "\n" in text else text
        if text.rstrip().endswith("```"): text=text.rstrip()[:-3]
    a=text.find("{"); b=text.rfind("}")
    if a>=0 and b>a:text=text[a:b+1]
    return json.loads(text)

def compare_companies_structured(ticker1,ticker2,data,filtered_positions,analysis_context=None):
    try:
        import streamlit as st
        api_key=st.secrets.get("OPENAI_API_KEY",os.getenv("OPENAI_API_KEY"))
        model=st.secrets.get("OPENAI_MODEL",os.getenv("OPENAI_MODEL","gpt-5.1"))
    except Exception:
        api_key=os.getenv("OPENAI_API_KEY"); model=os.getenv("OPENAI_MODEL","gpt-5.1")
    if not api_key:
        return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":"Falta configurar OPENAI_API_KEY en Streamlit Secrets."}
    ctx=compact(data,filtered_positions,selected_ticker)
    prompt=f"""Compará {ticker1} contra {ticker2} usando datos fundamentales actuales y verificables.
Obligatorio: P/E, Forward P/E, PEG y EV/EBITDA. Si un dato no aplica o no es significativo, devolvé null.
Usá búsqueda web. No inventes valores. Estos múltiplos son 'menor suele ser más favorable', pero no declares un ganador global sólo por eso.
En analysis considerá crecimiento, márgenes, balance, FCF, calidad y contexto de cartera. Indicá brevemente fuentes y fecha.
Contexto PMS: {json.dumps(ctx,ensure_ascii=False,default=str)}
Respondé SOLO JSON válido:
{{"company_a":"{ticker1.upper()}","company_b":"{ticker2.upper()}","metrics":[
{{"indicator":"P/E","a":null,"b":null}},
{{"indicator":"Forward P/E","a":null,"b":null}},
{{"indicator":"PEG","a":null,"b":null}},
{{"indicator":"EV/EBITDA","a":null,"b":null}}
],"analysis":"..."}}"""
    client=OpenAI(api_key=api_key)
    r=client.responses.create(model=model,instructions=SYSTEM_CONTEXT,input=prompt,tools=[{"type":"web_search"}])
    try:return _extract_json(r.output_text)
    except:return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":r.output_text or "No pude estructurar la comparación."}
