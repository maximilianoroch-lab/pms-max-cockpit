# Auditoría histórica LLY — 15/11/2026 (solo lectura)

**Problema:** las observaciones de `historial_precios` con precio ARS 23.100 repetido hasta 11/11/2026 no concilian con cotizaciones públicas de CEDEAR LLY cercanas a ARS 42.800. NO se deben reemplazar automáticamente registros históricos ni recalcular snapshots.

## Evidencias públicas (plaza/fecha; no completar espacios)

| Fecha | ARS por CEDEAR | Evidencia | Precaución |
| --- | ---: | --- | --- |
| 11/11/2026 | 42.800,00 | https://larueda.com.ar/datos/acciones/LLY/?denominacion=ARS&page=1 | Historial de LaRueda, confirmar modalidad de liquidación |
| 12/11/2026 | 42.820,00 | https://larueda.com.ar/datos/acciones/LLY/?denominacion=ARS&page=1 | Historial de LaRueda, confirmar modalidad de liquidación |
| 13/11/2026 | 43.100,00 | https://www.cohen.com.ar/Bursatil/Especie/LLY/MERVAL/24hs. | Cohen / BYMA, plazo 24hs, última actualización 13/11/2026 |

**Importante:** Cohen distingue cierre 24 horas de inmediato. Para 13/11, el precio *inmediato* difundido por Cohen fue ARS 43.740. No mezclar series con distinto plazo de liquidación. Los datos anteriores son evidencia inicial, no certificación definitiva de cierre homogéneo.

## Procedimiento de conciliación antes de modificar historia

1. Exportar `historial_precios` completo sin editar; identificar IDs, fechas, cantidades, moneda y fuente.
2. Determinar si ARS 23.100 es un fallback, precio stale, unidad errónea, ratio de CEDEAR o precio de otra rueda.
3. Confirmar precio y modalidad homogénea de **cada fecha** histórica afectada, además de ratio, fecha exacta de la fuente y conversión CCL/MEP del corte.
4. Identificar las posiciones y saldos efectivos por fecha; ningún precio de hoy reemplaza esos vectores.
5. Calcular reporte de diferencias, aprobar eventual corrección transaccional auditada; guardar el original y los cambios.
6. Solo después promover valores a `historial_precios` y recalcular el patrimonio histórico con reconciliación total.

Se agregó `ops/lly_history_audit.py` para producir un reporte read-only de anomalías a partir de un export CSV; el programa no se conecta a Sheets ni escribe en Google Drive. `ops/lly_public_reference_sample.csv` son referencias puntuales, **no** un histórico completo ni un feed de producción.


## Auditoría directa de Base PMS Bersoch (15/11/2026)

La búsqueda en `historial_precios` encontró **19 registros LLY** (08/10–11/11/2026). En los 19 figura exactamente **ARS 23.100** como precio unitario, a pesar de que todos se rotulan `Cotización automática`. La columna `Precio USD` y el valor total USD cambian por tipo de cambio, pero **esto no valida el precio LLY de mercado**. La constancia del mismo precio unitario en todas las fechas es un indicador de referencia obsoleta/fallback, no prueba de fraude ni de un precio corregido para las 19 fechas.

**Instrucción de auditoría:** revisar los 19 registros uno por uno contra cotizaciones fechadas de CEDEAR LLY, misma unidad, modalidad y plaza. La muestra externa documentada de 11–13/11 no se extrapola al mes anterior. Preservar los 19 originales y adjuntar evidencia antes de cualquier corrección. Nunca reetiquetar toda la serie como válida por haber hallado un precio para el 13/11.

## Contraste ampliado de historia — 15/11/2026

Fuente histórica consultable: https://www.larueda.com.ar/datos/acciones/LLY/?denominacion=ARS . LaRueda muestra cotizaciones diarias en ARS desde 08/10/2026 a 13/11/2026, con un historial de precio y volumen. **No** exhibe transacciones 09/11 ni 10/11, coherente con el calendario BYMA de días sin negociación. En la base real existen **19 filas LLY** (08/10 a 11/11), de las cuales **17 tienen fecha negociada** y las otras dos corresponden a 09/11 y 10/11; no son dos cotizaciones faltantes recuperables en BYMA.

Ejemplos de diferencias **por proveedor y sin homologar modalidad**:
- LaRueda: LLY cierre 08/10/2026 ARS 33.680; 19/10 ARS 36.040; 30/10 ARS 41.940; 06/11 ARS 40.760; **11/11 ARS 42.748,70**, **12/11 ARS 42.768,68**, **13/11 ARS 43.100**.
- El dato IOL aproximado citado antes fue ARS 42.800 para 11/11 y ARS 42.820 para 12/11. Una fuente pública alternativa (TwelveData BCBA) expone cierres redondeados y puede usar otra sesión/plazo de liquidación: https://twelvedata.com/markets/875636/stock/bcba/lly/historical-data . **No sustituir valores de una fuente por otra dentro de una misma serie sin validar mercado y liquidación.**

La serie de 19 precios constantes ARS 23.100 que consta en `historial_precios` es fuertemente sospechosa de stale/fallback: no debe interpretarse como fluctuación LLY real. Pero la validez de una corrección diaria todavía requiere confirmar unidad, plazo de liquidación, exactitud del proveedor, fecha de rueda, cantidad efectiva de 200 CEDEAR y tipo de cambio por corte antes de recalcular patrimonio.

**Decisión de auditoría:** conservar los registros 09–10/11 como observaciones patrimoniales multibolsa, etiquetar explícitamente `BYMA SIN NEGOCIACIÓN`, y no inventar precio LLY del día. Para los otros 17 registros, preparar comparaciones por fecha desde una única fuente homogénea antes de autorizar cualquier escritura. No distribuir CSVs masivos de cotizaciones bursátiles de terceros sin revisar términos de uso.
