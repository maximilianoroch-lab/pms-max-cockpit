# PMS Max · Cockpit v0.16

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

## v0.16 — Capas explícitas
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


## v0.16
Dashboard reforzado, contexto compartido, detalle de exposición, concentración por posición y proyecto listo para deploy en Streamlit Cloud.


## v0.16
Fix de arranque en Streamlit: `apply_analysis_context()` ahora se define antes de su primer uso.

## v0.16
- Fix de columnas normalizadas `Variación_num` e `Impacto cartera_num`.
- Corrige el KeyError que frenaba Resumen en Mayores movimientos.
- Evita mostrar `Precios: nan` cuando el estado no está disponible.

## v0.16
- Formato numérico homogéneo en español.
- Valores USD con separador de miles.
- Porcentajes visibles como porcentaje, no como fracción decimal.
- Encabezados de tablas y ejes sin sufijos técnicos `_num`.
- Ajuste visual de tarjetas KPI para evitar cortes de línea.

## v0.16
- Corrección de porcentajes en tablas: Peso y Variación ahora se muestran en puntos porcentuales reales.
- Formato consistente en Resumen, Evolución, Posiciones, Diversificación y Custodia.

## v0.16
- Patrimonio total como KPI principal a la izquierda.
- Crypto y Patrimonio sin Crypto agrupados en una misma tarjeta secundaria.
- Composición por clase más angosta; Mayores movimientos más ancho.
- Estados MEP/CCL desactualizados compactados a Último MEP / Último CCL.
- Nombres largos compactados en Mayores movimientos y Principales posiciones.
- Columnas de Estado más angostas y tipografía de tablas más compacta.

## v0.16
- Se elimina la tarjeta frontal de “Desglose”.
- El Resumen prioriza Patrimonio total, Argentina, Top 5 y Posiciones.
- Se agrega en Diversificación un gráfico de torta/donut “Cripto vs cartera convencional”.
- Colores del donut: Crypto en bordeaux oscuro y cartera convencional en azul/celeste.

## v0.16
- Custodia inicia en TODOS y conserva selección individual por custodio.
- Diversificación ordenada de mayor a menor, con dos tonos de azul diferenciados.
- Posiciones simplificada: se ocultan Custodio, Clase, Región y Sector.
- Fix robusto del stress test en Riesgo ante variaciones del nombre de columna de impacto.
- Se crea PRODUCT_BACKLOG.md y Evolución queda explícitamente pendiente de rediseño.

## v0.16
- En Diversificación, los títulos `Región` y `Sector` pasan arriba de cada gráfico.
- Se eliminan los títulos verticales laterales de los ejes Y.
- `Región`, `Sector` y `Cripto vs cartera convencional` usan la misma jerarquía tipográfica.

## v0.16
- Simulador corregido conceptualmente: distingue reasignación interna (usa/genera CASH y no cambia patrimonio) de aporte/retiro externo.
- Posiciones agrega vista Consolidado / Por cuenta.
- El Asesor IA muestra claramente si falta API key.
- Diversificación aclara la diferencia entre exposición ETF look-through y posiciones directas.
- Resumen incorpora un control de reconciliación de feeds dentro de un expander.
