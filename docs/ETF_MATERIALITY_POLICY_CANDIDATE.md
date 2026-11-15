# Propuesta de política de riesgo ETF — NO activada

El módulo `pms_etf_materiality.py` es independiente de fuentes y no escribe, alerta ni modifica la cartera. Opera sobre los resultados del motor parcial de solapamiento y las fechas de las fuentes, si se dispone legalmente de ellas.

**Parámetros candidatos para discutir antes de activar:**
- **1 % del patrimonio USD**: marcar un emisor identificado cuya exposición parcial directa + ETF supera ese peso.
- **2 % del patrimonio USD**: marcar la parte no desagregada de un ETF materialmente relevante. Que una exposición no esté identificada no implica que no exista riesgo.
- **30 días desde la fecha de holdings**: marcar una composición como antigua. La fecha de la fuente no acredita por sí sola actualidad de mercado.

Se muestran etiquetas de diagnóstico, **no recomendaciones** de compra/venta. El módulo nunca convierte cambios patrimoniales en rentabilidad ni calcula el solapamiento de un fondo sin fuente.

**Bloqueos para activación:** (1) los umbrales deben ser aceptados o corregidos por el titular; (2) las composiciones de los ETF deben obtenerse de una fuente que permita su tratamiento en el entorno donde se publicarán; (3) debe quedar clara la identificación de la especie y la relación ADR/CEDEAR/local; (4) ensayar sobre datos históricos y confirmar que no produzca alarmas falsas.

**Licencia:** la rama de fuentes #43 conserva solo un catálogo de URLs, sin redistribuir posiciones de iShares hasta revisar derechos de uso. Esta política funciona y se prueba con ejemplos sintéticos.
