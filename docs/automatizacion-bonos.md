# Automatización de bonos: diagnóstico y criterios de activación

## Estado verificado 2026-10-22
Bonos: AN29, AO28, AO29, GD35, GD38, GD41.
- `diagnostico_bonos_googlefinance`: fórmulas de prueba independientes. No alimentan cartera.
- `bonos_auto_v2`: encabezados A:H, sin filas de precios.
- `APPS_SCRIPT_V2!B3`: `actualizarAhora` y los triggers invocan `actualizarBonos`; dicha función no está definida en el módulo almacenado.
- `posiciones_v2`: `Valor USD` se deriva de cotizaciones manuales, `posiciones` y tipos de cambio; no existe lectura de `bonos_auto_v2`.

## Implementación pendiente, sin alterar datos contables
1. Seleccionar una fuente de mercado estable, con fecha, instrumento inequívoco, moneda y unidad de cotización (ARS cada 100 VN o USD cada 100 VN).
2. Implementar `actualizarBonos` en Apps Script **instalado**, comprobar permisos y crear triggers tras ensayos.
3. Escribir en `bonos_auto_v2` sólo cotizaciones positivas y verificables, con fecha de mercado, consulta, fuente, estado y nota. No sobrescribir último dato válido al fallar.
4. Verificar conversión a USD según convención de VN y tipo de cambio correcto. No multiplicar precio por cantidad sin dividir por 100 cuando corresponde.
5. Cambiar fórmula de valuación sólo cuando los seis símbolos estén mapeados y pruebas con cantidades verificadas arrojen resultados reconciliados. Mantener fallback manual visible y auditable.
6. Probar en copia de DEMO con datos ficticios antes de aplicar a PMS Bersoch; comparar posiciones por ticker, custodio y patrimonio total.
7. Validar días sin mercado, feriados, feeds vacíos, datos obsoletos y cotizaciones extremas; publicar fecha de mercado visible en UI.

**No activar fórmulas ni triggers mientras la fuente y la convención de precios no estén validadas.**
