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


## Hallazgo al inspeccionar Base PMS Bersoch (15/11/2026, solo lectura)

La pestaña `snapshot_series_v2` incluye entradas con fuente `Automático PMS` fechadas **09/11/2026** y **10/11/2026**, pese a que el calendario BYMA describe ambas como fechas sin negociación. Las sesiones estadounidenses y cripto pueden seguir activas, por lo que **no** debe borrarse el patrimonio de esos días ni declararse falso sin auditoría multicotización. Marcar temporalmente `BYMA_CERRADO_PATRIMONIO_MULTIMERCADO_REVISAR`.

Se suma `ops/snapshot_calendar_audit.py`: compara un CSV de `snapshot_series_v2` con un CSV de días sin negociación BYMA (por ejemplo, `ops/byma_no_trading_2026.csv` preparado en PR #32). Es totalmente **solo lectura** y no realiza cambios ni en Sheets ni en GitHub. Ejecutar una vez reunidos los archivos del mismo corte. Esta auditoría no reemplaza el requisito de recopilar precios por mercado.

**Fuente del calendario:** https://www.byma.com.ar/mercado/calendario-bursatil. El 06/11 se negoció sin liquidación y NO corresponde clasificarlo como rueda cerrada.

**Alerta adicional:** en `app_feed_v2`, la columna `Fecha dato` puede mostrar la hora de recálculo de la planilla (por ejemplo, domingo 15/11 a las 08:30) y no demuestra fecha de mercado por activo. No tratar ese sello de planilla como cierre bursátil certificado.
