# ETF look-through — consistencia temporal

El motor `pms_etf_overlap.py` solo estima solapamiento de los componentes principales de los ETF. Requiere `ETF,Constituyente,Peso ETF,Fuente,Fecha` con pesos fraccionales.

Esta mejora bloquea automáticamente la mezcla de dos fechas de composición dentro de un mismo ETF. Distintos ETF pueden tener cortes distintos; se informan como aproximaciones parciales. El archivo `etf_top_holdings.csv` **todavía no existe**, por lo que la app seguirá mostrando ausencia de cobertura respaldada.

**No cargar composiciones supuestas.** Próximo paso para la producción: obtener del emisor la composición oficial con fecha, conservar referencia/procedencia, controlar cobertura (suma <= 100 %) y identificar fracción sin desagregar. Si no hay fuente verificable, la función debe permanecer inactiva y nunca inventar exposición por sector/región.

No se modifican tenencias ni dashboards productivos.
