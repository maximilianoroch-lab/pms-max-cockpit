# Capture V3 — implementation review, NOT INSTALLED

## Verified defects in existing candidate (Base PMS Bersoch / APPS_SCRIPT_V2)
- 11:00 and 14:00 update MEP/bonds but do not preserve separate valuation observations.
- 17:00 writes legacy history, keyed only by date; a second run can overwrite the same day's instrument rows.
- Control `APTO` tests missing valuations, not that every ticker price is fresh as of the intended slot.
- Weekends are skipped, but market holidays are not modeled.
- `APPS_SCRIPT_V2` says `PREPARADO / NO INSTALADO`. This is document status, NOT proof of current Apps Script trigger state.

## Proposed safer workflow
1. Owner verifies existing Apps Script project and triggers first; do not install duplicates.
2. Create two new **separate** sheets:
   - `observaciones_intradiarias_v3`: twelve plain-text/number columns with headers
     `Snapshot ID,Fecha,Horario,Hora real,Estado,Ticker,Cantidad,Valor USD,Moneda,Fuente valor,Fecha actualización fuente,Observación`.
   - `feriados_mercado_v3`: first column `Fecha (AAAA-MM-DD)`; load and verify exchange holiday schedule, include a known explicit row (or marker; empty is blocked).
3. Review script with production user, confirm position count, price-source freshness, and time zone.
4. Run read-only data validation and a safe staging test before enabling 11/14/17 triggers.
5. Install at most one trigger per named handler; review execution logs and permissions.
6. Capture each slot append-only with unique date+slot ID. Repeated invocations return ALREADY_CAPTURED.
7. Label captures **OBSERVADO_NO_CERTIFICADO**, never promise observed close price without per-instrument timestamp and independent verification.
8. Promotion into `historial_precios` / `snapshot_series_v2` requires a separate audited process; no automatic promotion in this candidate.
9. Backfill November 12 and 13 only with verified historical holdings, prices, cash/FX and reconciliation. Never use Sunday's or Friday's latest price as a substitute.

## Known constraints
- The existing `posiciones_v2` does not provide a trustworthy market-close timestamp per security. A complete valuation can still be stale.
- Apps Script triggers scheduled near the hour do not guarantee exact executions.
- Argentine and relevant foreign market calendars may differ by security; this candidate uses an explicit controlled trading-day calendar and should not be deployed until agreed.
- The `pmsV3_1700` observation is not a legally or analytically certified closing snapshot.
- Until a persistent error-alert delivery channel is configured, failures will only be visible in script execution logs or existing freshness monitor.

## Acceptance checks before approval
- Re-run same slot: zero new rows.
- Non-trading day: zero new rows.
- Integrity not APTO or missing ticker value: zero new rows and visible error.
- Exactly one row per ticker in a successfully captured slot; totals reconcile.
- Stale quotes remain clearly unverified and cannot pollute the certified history.
- No changes to holdings, historical rows, live triggers, or the DEMO instance.

## Compatibilidad de calendarios (15/11/2026)
- El calendario `feriados_mercado_v3` representa **solo BYMA** y debe poblarse desde el calendario validado del PR #32 (fechas ISO `YYYY-MM-DD`, columna A).
- Si BYMA está cerrado un día lunes–viernes, la fotografía patrimonial **sí se conserva** para no perder actividad de activos internacionales o cripto, con etiqueta `OBSERVADO_BYMA_CERRADO_NO_CERTIFICADO`.
- En sábado y domingo no se programan estas tres observaciones (aunque cripto opere 24/7). Una futura captura cripto 24/7 sería un proceso distinto.
- La fotografía completa nunca certifica cierre de ninguno de los mercados y no ingresa automáticamente en el histórico.
- El horario de Apps Script debe estar configurado en America/Argentina/Buenos_Aires y la función rechaza disparadores fuera de su hora local.
- Aunque PR #31 y PR #32 pasen pruebas separados, el calendario/hojas/disparadores deben revisarse juntos antes de instalar.

## BYMA horario de cierre revisado — 15/11/2026

La comunicación oficial BYMA **19031** de 28/10/2026 modificó horarios desde el 02/11/2026 (https://www.byma.com.ar/comunicados/com19031-horarios). Para acciones y CEDEAR, el cierre de negociación informado es **18:00 ART**, de modo que `pmsV3_1700` es **observación intradiaria**, NO cierre EOD. Mantener 11:00 / 14:00 / 17:00 como se acordó, sin convertir automáticamente la última observación en cierre de mercado. Para un cierre posterior a las 18:00 hace falta diseñar un proceso separado con confirmación de fuente, rezagos, plaza y fecha de precio por ticker; un mero trigger a las 18:30 no certifica el cierre.

Las restricciones de negociación/liquidación del 06/11 y 11/11 de 2026 no equivalen a fin de semana. Las observaciones de 09/11 y 10/11 se conservan para portfolio multibolsa, marcadas BYMA cerrado. Fuente: https://www.byma.com.ar/mercado/calendario-bursatil.

## Marcas de actualización de planilla vs cotización

La columna `Fecha actualización` de `posiciones_v2` puede contener números seriales de Google Sheets (ej. `46341,41616`) o un objeto Date. **No son una prueba de fecha de operación en mercado** y nunca se deben rotular como cotización actualizada. El capturador conserva el valor con prefijo `PLANILLA_SERIAL_NO_MERCADO:` o `PLANILLA_NO_MERCADO:`; si no hay fecha guarda `SIN_FECHA_FUENTE_VERIFICADA`. La última columna de observación sigue indicando que falta una prueba de frescura por ticker. Un cierre verificado requiere fuente con hora y plaza por instrumento, además de la integridad de cantidades.
