# Fuente de precios para seis bonos — decisión técnica (22/10/2026)

**Estado:** ninguna API de mercado está activada ni integrada a la valuación. Este documento no autoriza transacciones.

## Evidencia de proveedores
- BYMA EOD: precio de cierre de renta fija; la página vigente de APIs indica **solo agentes miembros BYMA** para End of Day. No asumir acceso minorista ni tarifa gratuita. Fuente: https://www.byma.com.ar/byma-apis
- IOL: API documentada con cotizaciones históricas y actuales de bonos; requiere cuenta abierta, solicitud de activación desde Mensajes y aceptación de términos en Mi Cuenta > Personalización > APIs. El acceso puede tener cargo según tarifas. Fuente: https://www.invertironline.com/api y https://developers.invertironline.com/
- Data912 /live/arg_bonds: expone symbol/c/volumen y libro de ofertas, sin campos documentados de moneda, fecha de rueda ni VN base por cada precio; por tanto es solo referencia experimental. Fuente: https://data912.apidocs.ar/operations/getliveargbonds

## Orden recomendado
1. Verificar si ya existe una cuenta IOL con permiso de API **solo lectura**. No solicitar datos de acceso ni pegar tokens en GitHub o Sheets.
2. Consultar al broker actual (Criteria u otro custodio) si ofrece cotizaciones EOD exportables con símbolos, especie, fecha, moneda y unidad.
3. Evaluar servicio licenciado BYMA mediante canal habilitado si no hay proveedor viable.
4. Crear adaptador de solo lectura que entregue exactamente {symbol,market,currency,nominal_basis,price,market_date,source}.
5. Ejecutar bond_quote_validation.py; registrar rechazos sin reemplazar última cotización validada.
6. Comparar cierre y valor calculado contra extracto de custodio por los seis tickers; aprobar integración **solo** si diferencia dentro de redondeos conocidos.
7. Instalar triggers y conectar bonos_auto_v2 a posiciones_v2 **después** de ensayos en copia DEMO aislada. No usar la fuente experimental como default.

## Bloqueos reales
- Permisos y credenciales de proveedor no disponibles aquí.
- Mapeo de especies y base VN de cada ticker no verificados contra extractos.
- Triggers Apps Script no instalados y pipeline Sheets sin conexión.
