# Bonos — diagnóstico solamente, sin escritura

Este candidato reemplaza el PR histórico #3, cuya rama antigua no está alineada con el código actual. Se trabaja desde `main`, sin reproducir la función `actualizarBonos` que escribía en `bonos_auto_v2`.

`ops/Bonos_Diagnostico_SoloLectura_V2.gs` verifica únicamente si la página pública IOL de AN29, AO28, AO29, GD35, GD38 y GD41 devuelve HTML con fechas. No infiere precio, divisa, precio por 100 VN, modalidad de liquidación, validez temporal ni cierre. Por diseño, **siempre** devuelve `certificate:false` y `priceUsableForValuation:false`.

Bloqueos antes de una automatización que escriba precios:
1. Confirmar que existe una API autorizada o un parser documental con estructura y términos de uso controlados.
2. Validar para cada especie: ticker, denominación/moneda, monto por VN, plazo, hora y fecha de mercado.
3. Contrastar cotizaciones fechadas con una segunda fuente confiable y auditar bonos reales contra efectivo USD.
4. Solo entonces diseñar un promotor separado, con pruebas de idempotencia y rechazo de valores desactualizados. No reutilizar un parser indicativo como escritura.

No hay triggers, instalación, cambios de Sheets ni datos patrimoniales.
