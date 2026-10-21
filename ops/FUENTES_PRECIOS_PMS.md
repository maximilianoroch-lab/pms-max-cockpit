# PMS — Política de fuentes, 21/10/2026

- **Bonos AN29, AO28, AO29, GD35, GD38, GD41**: el método figura `bono_auto` pero `bonos_auto_v2` no tiene filas; el feed utiliza `CARGA_DIARIA manual` (15/10/2026). No etiquetar como automático ni recalcular su valor sin prueba de especie, divisa, unidad de cotización (ARS por 100 VN) y fecha.
- **FUT**: valuación manual por diseño.
- **BYMA**: la API EOD tiene plan gratuito **para miembros**, pero las APIs Market Data no están disponibles actualmente para personas físicas (FAQ oficial https://www.byma.com.ar/productos/productos-de-datos/market-data/apis). No suponer acceso individual.
- **Apps Script**: falta acceso de administración del proyecto para inspeccionar logs, instalar triggers y ejecutar el módulo. No activar `actualizarBonos` sin diagnóstico previo.
- **MEP**: error del trigger observado el 21/10/2026 a las 11:03; causa no determinada. No modificar tipos de cambio ni activadores sin el log.
- **Datos de flujos**: `flujos_v2` recuperada de error #REF!; retiro IOL 10/03/2026 confirmado -539118 ARS y -366 USD; una copia anterior queda resguardada. No certificar retornos históricos hasta conciliar movimientos.
- **Auditoría automática de fuente**: tab oculta `auditoria_fuentes_v2` de Google Sheets con las 7 especies, fuente y estado actual derivado de `app_feed_v2` y presencia en `bonos_auto_v2`.

## Criterios de aceptación

1. Consultar proveedor de precios por especie y capturar fuente/fecha/moneda/unidad; rechazar datos faltantes o antiguos.
2. Verificar muestra de cada bono contra un segundo origen y contra la fórmula de USD antes de promover.
3. Mantener fallback manual identificado cuando no hay dato confiable.
4. Probar Apps Script de solo lectura antes de instalar escritura/activadores.
5. Enviar a dashboards estado REAL de precio y diferenciar variación patrimonial de rentabilidad neta.
