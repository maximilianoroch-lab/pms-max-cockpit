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
