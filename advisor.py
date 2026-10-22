
import os,json,re,pandas as pd
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError, BadRequestError
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
Separá claramente:
1) Datos internos de esta cartera.
2) Información externa consultada en la web.
Para fundamentales, noticias, valuaciones o hechos recientes usá búsqueda web. No inventes datos.
Cuando uses información externa, indicá fecha de referencia y dejá visibles las fuentes/citas aportadas por la búsqueda.
No decidas por el usuario: presentá evidencia, contradicciones, riesgos y escenarios.
- Redactá Markdown estricto y limpio: espacio después de **, párrafos separados, sin HTML embebido, sin cursiva accidental ni asteriscos contiguos incompletos. No uses tablas para prosa ni URLs dentro de palabras.
Reglas de calidad del análisis:
- NO generes alertas de inconsistencia comparando por tu cuenta `app_feed_v2`, `filtered_positions` y `looker_feed_v2`. Esos feeds pueden tener alcances distintos.
- Sólo llamá "inconsistencia" a un problema que venga marcado explícitamente por el PMS en un campo/alerta de calidad de datos. Si no existe esa alerta explícita, no la inventes.
- Para un ticker mencionado en la consulta, usá `mentioned_ticker_details` como detalle por cuentas, pero no lo uses para auditar o reconciliar el consolidado salvo que el PMS lo marque como control verificado.
- Si falta una fila o una cuenta en el contexto, tratala como "detalle no visible/no disponible", nunca como discrepancia confirmada.
- Formato obligatorio por defecto:
  1) `## Resumen ejecutivo`: 4 a 6 bullets, máximo 90 palabras.
  2) `## Desarrollo`: máximo 3 secciones, sólo evidencia y razonamiento que agreguen algo al resumen.
  3) `## Conclusión`: 1 párrafo corto, condicionado y sin repetir los bullets.
- Extensión total objetivo por defecto: 350 a 500 palabras. Si el usuario pide profundidad, ampliar hasta aproximadamente 900 a 1.200 palabras.
- Priorizá 5 a 8 hallazgos materiales. No repitas la misma idea en varias secciones.
"""

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

def compact(data,filtered,selected_ticker="",user_prompt=""):
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
    mentioned=[]
    detail_full=data.get("looker_feed_v2",pd.DataFrame()).copy()
    prompt_upper=str(user_prompt or "").upper()
    known_tickers=[]
    if not app.empty and "Ticker" in app.columns:
        known_tickers=sorted(app["Ticker"].dropna().astype(str).unique().tolist(),key=len,reverse=True)
    for t in known_tickers:
        # Token-aware enough for portfolio tickers; avoids matching T inside arbitrary words.
        if re.search(r"(?<![A-Z0-9])"+re.escape(t.upper())+r"(?![A-Z0-9])",prompt_upper):
            mentioned.append(t)
    if selected_ticker and selected_ticker not in mentioned:
        mentioned.append(selected_ticker)

    mentioned_details={}
    if mentioned and not detail_full.empty and "Ticker" in detail_full.columns:
        for t in mentioned:
            dd=detail_full[detail_full["Ticker"].astype(str)==str(t)].copy()
            cols=[c for c in ["Ticker","Nombre","Custodio","Cuenta","Cantidad","Valor USD_num","Peso cartera_num",
                              "Clase","Tipo","Región directa","Sector directo","Estado dato","Variación_num"] if c in dd.columns]
            if not dd.empty:
                mentioned_details[t]={
                    "rows":dd[cols].sort_values("Valor USD_num",ascending=False).fillna("").to_dict("records"),
                    "detail_total_usd":float(dd["Valor USD_num"].sum()) if "Valor USD_num" in dd.columns else None,
                    "accounts":sorted(dd["Cuenta"].dropna().astype(str).unique().tolist()) if "Cuenta" in dd.columns else [],
                    "custodians":sorted(dd["Custodio"].dropna().astype(str).unique().tolist()) if "Custodio" in dd.columns else []
                }

    return {
        "top_positions":top,
        "filtered_positions_partial_DO_NOT_RECONCILE":f,
        "selected_ticker":selected,
        "mentioned_tickers":mentioned,
        "mentioned_ticker_details":mentioned_details,
        "context_rules":{
            "filtered_positions_is_partial": True,
            "do_not_reconcile_feeds": True,
            "only_surface_verified_data_quality_alerts": True
        },
        "risk":risk.head(25).fillna("").to_dict("records"),
        "exposure":expo.head(20).fillna("").to_dict("records")
    }

def ask_advisor(user_prompt,data,filtered_positions,history=None,selected_ticker="",analysis_context=None):
    try:
        import streamlit as st
        api_key=st.secrets.get("OPENAI_API_KEY",os.getenv("OPENAI_API_KEY"))
        model=st.secrets.get("OPENAI_MODEL",os.getenv("OPENAI_MODEL","gpt-5.6"))
    except Exception:
        api_key=os.getenv("OPENAI_API_KEY");model=os.getenv("OPENAI_MODEL","gpt-5.6")
    if not api_key:
        return "El dashboard funciona, pero el Asesor IA todavía no tiene OPENAI_API_KEY configurada en los Secrets de Streamlit."
    ctx=compact(data,filtered_positions,selected_ticker,user_prompt=user_prompt)
    messages=[]
    for m in (history or [])[-6:]:
        if m.get("role") in ("user","assistant"):messages.append({"role":m["role"],"content":m["content"]})
    ctx["analysis_context"]=analysis_context or {}
    prompt=(
        "CONTEXTO ACTUAL DEL PMS:\n"+json.dumps(ctx,ensure_ascii=False,default=str)
        +"\n\nCONSULTA:\n"+user_prompt
        +"\n\nFORMATO OBLIGATORIO POR DEFECTO: "
         "abrí con `## Resumen ejecutivo` de 4 a 6 bullets y máximo 90 palabras; "
         "seguí con `## Desarrollo` de hasta 3 secciones; cerrá con `## Conclusión` de un párrafo corto. "
         "La respuesta completa debe quedar normalmente entre 350 y 500 palabras. "
         "Si el usuario pide explícitamente profundidad, podés ampliar hasta aproximadamente 900 a 1.200 palabras. "
         "No audites ni reconcilies feeds entre sí y no inventes inconsistencias. No repitas conclusiones."
    )
    client=OpenAI(api_key=api_key)
    try:
        response=client.responses.create(
            model=model,
            reasoning={"effort":"low"},
            instructions=SYSTEM_CONTEXT,
            input=messages+[{"role":"user","content":prompt}],
            tools=[{"type":"web_search","search_context_size":"medium"}],
        )
        return response.output_text
    except AuthenticationError:
        return "No pude autenticar la API de OpenAI. Revisá OPENAI_API_KEY en Streamlit Secrets."
    except RateLimitError as e:
        msg=str(e)
        if "credit_balance_exhausted" in msg or "no credits remaining" in msg.lower():
            return "La API está autenticada, pero no tiene saldo disponible. Cargá créditos en la cuenta de API de OpenAI."
        return "La API alcanzó un límite temporal. Esperá unos segundos y volvé a intentar."
    except APIConnectionError:
        return "No pude conectarme con la API de OpenAI. Probá nuevamente en unos segundos."
    except BadRequestError as e:
        return f"La API rechazó la consulta. Detalle técnico: {str(e)[:220]}"
    except Exception:
        return "El Asesor IA encontró un error inesperado. El Dashboard sigue funcionando; revisá los logs si el problema se repite."


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
        model=st.secrets.get("OPENAI_MODEL",os.getenv("OPENAI_MODEL","gpt-5.6"))
    except Exception:
        api_key=os.getenv("OPENAI_API_KEY"); model=os.getenv("OPENAI_MODEL","gpt-5.6")
    if not api_key:
        return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":"Falta configurar OPENAI_API_KEY en Streamlit Secrets."}
    ctx=compact(data,filtered_positions,user_prompt=f'{ticker1} {ticker2}')
    ctx["analysis_context"]=analysis_context or {}
    prompt=f"""Compará {ticker1} contra {ticker2} usando datos fundamentales actuales, homogéneos y verificables.
Primero identificá el sector/tipo de ambas empresas. Mostrá EXCLUSIVAMENTE indicadores relevantes:
- Empresas no financieras: P/E, Forward P/E, PEG, EV/EBITDA, ROE, ROIC, crecimiento anualizado de ingresos 3-5 años, crecimiento anualizado EPS 3-5 años y Free Cash Flow.
- Bancos: P/E, Forward P/E, ROE, ROA, crecimiento anualizado de ingresos 3-5 años (sólo si comparable), crecimiento EPS 3-5 años, NIM, morosidad, cobertura de mora, ratio de eficiencia y capital regulatorio.
- Otras financieras: adaptá selectivamente según sentido económico.
NO incluyas EV/EBITDA, ROIC, PEG o FCF convencional para bancos. NO muestres métricas no pertinentes.
Si falta un dato, usá null; no inventes. Si ambos valores faltan, omití la métrica.
Para crecimientos usá CAGR calculada con cifras históricas, no estimaciones sin identificarlas. Preferí series homogéneas. Para métricas % enviá números en puntos porcentuales (12.3 significa 12,3%).
Usá búsqueda web y fuentes primarias cuando sea posible; indicá fechas y limitaciones de comparabilidad.
En bullets escribí 4 a 6 puntos breves y contrastantes, con ventajas/desventajas EXPLÍCITAS por ticker; evitá un empate vago.
En analysis escribí un desarrollo de extensión moderada (aprox 350 a 550 palabras), con riesgos, fortalezas, contexto PMS, balance y conclusión condicionada. No repitas todos los bullets.
«Favorece» de cada fila es orientación por métrica, no decisión global. Para indicadores bancarios usá las denominaciones estándar y marcá comparable:false si los períodos o definiciones impiden una comparación justa. Explicá en cada fila las métricas no estándar con description breve. No confundas cobertura de mora con garantías.
Contexto PMS: {json.dumps(ctx,ensure_ascii=False,default=str)}
Respondé SOLO JSON válido, sin markdown externo, con esta forma:
{{"company_a":"{ticker1.upper()}","company_b":"{ticker2.upper()}",
"metrics":[{{"indicator":"P/E","a":12.5,"b":16.0,"unit":"x","relevant":true}},
{{"indicator":"ROE","a":13.2,"b":10.4,"unit":"%","relevant":true}}],
"bullets":["A FAVOR {ticker1.upper()}: ...","A FAVOR {ticker2.upper()}: ...","RIESGO {ticker1.upper()}: ...","RIESGO {ticker2.upper()}: ..."],
"analysis":"..."}}"""
    client=OpenAI(api_key=api_key)
    try:
        r=client.responses.create(
            model=model,
            reasoning={"effort":"medium"},
            instructions=SYSTEM_CONTEXT,
            input=prompt,
            tools=[{"type":"web_search","search_context_size":"medium"}],
        )
    except AuthenticationError:
        return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":"No pude autenticar la API de OpenAI. Revisá OPENAI_API_KEY en Streamlit Secrets."}
    except RateLimitError as e:
        msg=str(e)
        if "credit_balance_exhausted" in msg or "no credits remaining" in msg.lower():
            msg="La API está autenticada, pero no tiene saldo disponible."
        else:
            msg="La API alcanzó un límite temporal. Probá nuevamente en unos segundos."
        return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":msg}
    except APIConnectionError:
        return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":"No pude conectarme con la API de OpenAI."}
    except Exception:
        return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":"No pude completar la comparación en este momento."}
    try:return _extract_json(r.output_text)
    except:return {"company_a":ticker1.upper(),"company_b":ticker2.upper(),"metrics":[],"analysis":r.output_text or "No pude estructurar la comparación."}
