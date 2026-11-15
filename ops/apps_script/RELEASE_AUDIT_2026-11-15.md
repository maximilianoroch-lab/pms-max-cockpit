# Auditoría de preparación — 2026-11-15 (sin instalación)

## Confirmaciones con fuentes conectadas
- **Base PMS Bersoch**: hoja `control_integridad_v2`: 66/66 posiciones, 0 sin valor, estado `APTO`. Esta comprobación **no** demuestra frescura por instrumento.
- **Base PMS Bersoch**: `snapshot_series_v2` termina en 2026-11-11. Las fechas 2026-11-12 y 2026-11-13 no aparecen en la serie consultada. No rellenar con precios actuales.
- **Base DEMO PMS Max**: `snapshot_series_v2` solo muestra una secuencia hasta 2026-10-21; requiere un historial ficticio/independiente y correctamente etiquetado, no copiar patrimonio real.
- **Auditoría de fuentes de Bersoch**: AN29, AO28, AO29, GD35, GD38 y GD41 figuran `MANUAL DESACTUALIZADO`; FUT figura manual por diseño. No afirmar que la totalidad de la cartera tiene precios actualizados.
- `APPS_SCRIPT_V2` documenta `PREPARADO / NO INSTALADO`; el estado real de los disparadores de Apps Script **no** se verifica desde esa etiqueta.
- En PR #31 se agregó un job de CI offline para `SnapshotCaptureV3.gs` usando simuladores, sin tocar planillas.

## Estado separado del trabajo
| Requisito | Estado al registrar |
|---|---|
| Código V3 de observaciones append-only | Desarrollado, borrador |
| Pruebas simuladas de calendario, duplicados y 11/14/17 | CI específico aprobado en GitHub |
| Verificación de fuente y timestamp por ticker | Pendiente, bloqueo de certificación |
| Modelo de días sin rueda por mercado/instrumento | Pendiente, bloquear instalación |
| Disparadores reales existentes en Apps Script | No comprobados |
| Prueba de extremo a extremo con planilla staging | Pendiente |
| Instalación y triggers productivos | No ejecutados |
| Recuperación certificada de 12 y 13 de noviembre | Pendiente de fuentes históricas y conciliación |
| Historial propio DEMO | Pendiente de fuente y trazabilidad |
| Alertas de errores y retrasos | Pendiente de configuración de canal de entrega |

## Criterios de liberación
1. Inventariar los disparadores instalados y sus funciones antes de habilitar otros; no duplicar handlers.
2. Documentar en un calendario verificable los días bursátiles pertinentes para cada fuente o instrumento.
3. En caso de precios sin fecha/hora/fuente verificables, registrar solo observación **no certificada** o bloquear; nunca publicar cierre auditado.
4. Prueba en staging para los tres horarios, duplicados, no-rueda, bloqueo, fallos parciales y alerta.
5. Auditar denominación, moneda, unidad, FX y tenencias al reconstruir cierres históricos. No alterar cartera sin conciliación y autorización específica.
6. Respetar la separación de datos entre PMS Bersoch y DEMO PMS Max.
7. Instalar en lote únicamente después de la aprobación de Max; realizar respaldo y plan de reversión.

Este archivo registra evidencia y pendientes; no equivale a despliegue.
