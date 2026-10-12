# PMS Max · Cockpit v0.9

Esta es la instancia privada de **PMS Max**.

## Arquitectura
- `app.py`: interfaz Streamlit.
- `data.py`: lectura y normalización de feeds.
- `advisor.py`: asesor IA y comparadores.
- `portfolio_config.py`: identidad, fuente de datos y reglas específicas de PMS Max.
- `.streamlit/`: configuración visual y ejemplo de secrets.

## Aislamiento
PMS Max debe desplegarse de forma independiente de cualquier otra cartera.

No usar:
- selector multi-cartera,
- Google Sheet compartida,
- repositorio con datos de otra cartera,
- memoria/chat compartido entre instancias.

Una futura **PMS Grupo** debe tener:
- otro Google Sheet,
- otro repositorio o paquete de deploy,
- otro archivo `portfolio_config.py`,
- otros Secrets,
- otro deploy de Streamlit,
- contexto del asesor independiente.

El código base puede reutilizarse, pero **los datos y configuraciones no se comparten**.

## Asesor IA
Incluye consulta libre y acciones guiadas:
- Analizar cartera
- Analizar ticker
- Comparar empresas
- Consultar fundamentales
- Consultar noticias
- Explicar movimiento
- Simular operación

## Ejecutar
`pip install -r requirements.txt`
`streamlit run app.py`

El dashboard funciona sin API key. El asesor requiere `OPENAI_API_KEY`.

## v0.9 — Capas explícitas
PMS Max Cockpit queda dividido conceptualmente en:

1. Dashboard
   - Resumen
   - Diversificación
   - Evolución
   - Riesgo
   - Custodia
   - Posiciones

2. Herramientas analíticas
   - Comparador de empresas
   - Simulador de operación

3. Asesor IA
   - Chat libre
   - Acciones guiadas
   - Contexto de cartera

El Dashboard sigue siendo autónomo: ninguna métrica básica obliga a usar IA.

### Simulador
El Simulador calcula de manera determinística el impacto de comprar/vender un monto USD:
- valor de la posición,
- peso de la posición,
- patrimonio total,
- concentración Top 5.

Luego permite enviar ese escenario al Asesor IA para interpretación.


## v0.9
Dashboard reforzado, contexto compartido, detalle de exposición, concentración por posición y proyecto listo para deploy en Streamlit Cloud.


## v0.9
Fix de arranque en Streamlit: `apply_analysis_context()` ahora se define antes de su primer uso.

## v0.9
- Fix de columnas normalizadas `Variación_num` e `Impacto cartera_num`.
- Corrige el KeyError que frenaba Resumen en Mayores movimientos.
- Evita mostrar `Precios: nan` cuando el estado no está disponible.
