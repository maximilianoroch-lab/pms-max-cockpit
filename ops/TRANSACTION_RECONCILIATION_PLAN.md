# Operaciones informadas pendientes de conciliación — procedimiento seguro

**Control realizado el 15/11/2026**: la lectura de Base PMS Bersoch no mostró importes exactos de los cuatro movimientos recientes informados dentro de `movimientos`, `ingesta_operaciones`, `ingesta_flujos` u `operaciones_normalizadas`. La pestaña `app_custodia_detalle_v2` seguía mostrando posiciones de MSFT en Adcap y no mostraba GOOGL en Galicia. Esto **no** demuestra inexistencia del movimiento en cada entidad financiera; sí demuestra que la representación del PMS no está conciliada con lo informado.

Los cuatro eventos ya están descritos en el historial de conversaciones, por lo que **no** duplicamos aquí importes, cuentas personales ni precios. Antes de escribir en la base, falta la **fecha efectiva** y debe comprobarse si algún movimiento fue aplicado por una vía diferente. Se requiere consultar comprobantes y asiento original. Evitar deducir fecha de la hora del chat.

Se preparó `ops/transaction_reconciliation_preflight.py`, herramienta local solo lectura con encabezados CSV:

- operaciones: `Referencia,Fecha,Broker,Ticker,Movimiento,Cantidad,Importe,Moneda`
- custodia: `Broker,Ticker,Cantidad`

La herramienta valida referencia única, importes, cantidades y fechas obligatorias. **Nunca** carga transacciones, cambia custodia o reescribe historia. Si falta fecha, lo reporta; si existe, lo deja como pendiente de registro o conciliación hasta evidencia independiente. Su salida debe revisarse y no publicarse si contiene montos personales.

**Bloqueo real:** confirmar fecha de operación de venta, compra, depósito y retiro, y revisar si fueron asiento interno entre brokers o flujos externos hacia/desde el PMS. Este carácter cambia el cálculo de rentabilidad y no debe inferirse.

Al resolver la fecha, preparar un conjunto de asientos reversibles, identificados por fuente y comprobante, con control de efectivo en ARS, títulos por custodio y comprobación de patrimonio. Luego solicitar autorización antes de escribir datos reales.
