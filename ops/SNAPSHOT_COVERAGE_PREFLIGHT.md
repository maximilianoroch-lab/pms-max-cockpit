# Reconciliación preliminar de cierres — 12 y 13 de noviembre de 2026

`ops/snapshot_coverage_preflight.py` no reconstruye cierres. Compara **dos CSV exportados o documentados** y marca las cotizaciones por fecha e instrumento que faltan.

Ejemplo de entradas (encabezados):

- Tenencias fechadas: `Fecha,Ticker,Cantidad`.
- Cotizaciones fechadas: `Fecha,Ticker,Precio,Moneda,Fuente,Corte`.

Ejecutar:

```bash
python -m ops.snapshot_coverage_preflight --positions tenencias_fechadas.csv --quotes cotizaciones_fechadas.csv --dates 2026-11-12 2026-11-13
```

La herramienta no accede a Google Sheets y no consulta ni modifica cuentas. El resultado `COBERTURA_PRELIMINAR_COMPLETA` solo significa que cada activo con cantidad positiva **tiene** una cotización de esa fecha con precio positivo, moneda, fuente y corte informados. **No certifica** que el precio sea verdadero, corresponda a la plaza o modalidad correcta, ni que las cantidades hayan sido auditadas. Tampoco certifica caja, divisas, ratio de CEDEAR, precio de bonos por VN, FUT, dividendos, movimientos ni patrimonio.

Por seguridad, este preflight es un requisito informativo y **nunca promueve datos a `historial_precios` o `snapshot_series_v2`**. Los archivos privados de posiciones se operan localmente o con permisos autorizados, nunca se adjuntan a CI.

Activación de cierres retroactivos: solo después de conseguir exports fechados, completar brechas, conciliar cotizaciones/plazos/caja/FX y aprobar una reconstrucción auditada. No usar precios actuales ni inventar cotizaciones.
