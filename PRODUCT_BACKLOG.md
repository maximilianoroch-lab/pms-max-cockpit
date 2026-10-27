# PMS Bersoch / DEMO PMS Max — pendientes de escritorio y mobile

## Objetivo vigente: cuatro bloques antes de automatizar fuentes

### 1. Evolución 2.0 — EN CURSO
- [x] Selector de ventanas observadas (1M/3M/6M/1A/3A/5A/Todo) en ambos escritorios.
- [x] Filtrado sin interpolar fechas ni presentar cambios patrimoniales como rentabilidad.
- [ ] Mejorar contexto visual de la serie y contraste contra benchmarks cuando existan fuentes homologadas.
- [ ] Separar aportes/retiros del desempeño **solo** cuando se disponga de movimientos conciliados.
- [ ] Mantener bloque Top 15 y habilitar saltos a contexto del ticker donde aplique.

### 2. Navegación / drill-down — EN CURSO
- [x] DEMO escritorio: filtrar exposición por región y sector y navegar a IA, Comparar y Simulador.
- [x] Bersoch: desde distribución geográfica/sectorial se puede aplicar contexto global.
- [ ] Homologar los recorridos completos, incluidos accesos desde Evolución y Custodia.
- [ ] Evaluar retiro del selector visual “—” preservando los controles de estado de Streamlit.

### 3. Riesgo y ETF top holdings — MOTOR LISTO / DATOS PENDIENTES
- [x] Motor compartido `pms_etf_overlap.py`: cálculo limitado a holdings principales por ETF.
- [x] Tope configurable de constituyentes, validación de pesos, fuente y fecha.
- [x] Presentar por separado la fracción **sin desagregar**; no inferir exposición exacta de ETF.
- [ ] Conectar un conjunto pequeño y fechado de posiciones principales por ETF a la UI de riesgos.
- [ ] Mostrar solapamiento significativo por emisor/sector/región sin fingir cobertura del 100 %.
- [ ] Acordar umbral de materialidad y política de refresco en la etapa de automatización.

### 4. Homologación escritorio / mobile — EN CURSO
- [x] Ambos escritorios: controles automáticos y evolución con mismas ventanas.
- [x] DEMO mobile: reemplazada fuente real escalada ×4 por inventario independiente V5; validaciones de 65 tickers, cuentas e importes.
- [x] DEMO mobile: pruebas de aislamiento, navegador, lectura y sintaxis.
- [x] Bersoch mobile: título de la aplicación corregido.
- [ ] Certificar visualmente mobile real y DEMO en dispositivos, incluida carga de inventario y estado offline.
- [ ] Alinear funcionalidades móviles avanzadas (el DEMO mobile dirige IA/Comparar/Simulador al escritorio independiente).

## Regla de precisión
Las cotizaciones DEMO son indicativas. Los históricos observados no se convierten en rendimiento financiero. En ETF, mostrar pocos componentes importantes y su cobertura total; todo peso no explicado queda explícito como **no desagregado**.

## Automatización de fuentes
Se evaluará después de revisar el desarrollo benchmark aportado por el usuario. No integrar cotizaciones o movimientos de otra cartera.
