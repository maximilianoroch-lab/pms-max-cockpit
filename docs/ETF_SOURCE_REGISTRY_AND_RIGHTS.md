# Fuentes oficiales ETF — candidato sin datos reutilizables

Se identificaron fuentes oficiales y fechas de referencia de SPY, QQQ, XLV, ACWI, FXI, EEM y EWZ (metadatos en `ops/etf_sources_registry.csv`). Estas fechas describen **fotografías históricas**, no composición vigente.

**No se distribuyen ni se incorporan holdings ni pesos en este repositorio público.** Los archivos descargables de iShares advierten restricciones de uso y redistribución; además deben revisarse las condiciones aplicables de State Street e Invesco antes de publicar sus composiciones. El hecho de que una fuente sea accesible y verificable no otorga permiso para copiarla a un dashboard público.

La capa `pms_etf_overlap.py` está probada, pero no se debe crear `etf_top_holdings.csv` en este repositorio hasta confirmar licencia o fuente reutilizable. En ausencia de ese archivo, la aplicación debe mostrar que no hay desagregación oficial disponible, sin inventar pesos.

Próximos pasos: (1) revisar términos y autorizaciones; (2) verificar identificadores y fecha por mercado (acciones locales de Hong Kong, Brasil, Taiwan, Corea, India no son necesariamente equivalentes a ADR/CEDEAR); (3) integrar datos autorizados con cobertura parcial explícita; (4) probar la UI y fecha de actualización; (5) mantener GLD como exposición a oro, no como cesta accionaria.

Este registro de referencias no modifica la cartera, Sheets, el despliegue ni los históricos. 
