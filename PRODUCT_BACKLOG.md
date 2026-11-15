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
- [x] Acceso desde Top 15 de Evolución al Asesor IA con ticker activo.
- [ ] Homologar los recorridos completos, incluidos accesos desde Custodia.
- [ ] Evaluar retiro del selector visual “—” preservando los controles de estado de Streamlit.

### 3. Riesgo y ETF top holdings — MOTOR LISTO / DATOS PENDIENTES
- [x] Motor compartido `pms_etf_overlap.py`: cálculo limitado a holdings principales por ETF.
- [x] Tope configurable de constituyentes, validación de pesos, fuente y fecha.
- [x] Presentar por separado la fracción **sin desagregar**; no inferir exposición exacta de ETF.
- [x] Preparar lectura optativa de composiciones principales fechadas en la vista Riesgo, sin generar estimaciones si el archivo fuente falta.
- [ ] Incorporar el conjunto real y fechado de principales componentes por ETF tras revisar el benchmark.
- [ ] Mostrar solapamiento significativo por emisor/sector/región sin fingir cobertura del 100 %.
- [ ] Acordar umbral de materialidad y política de refresco en la etapa de automatización.

### 4. Homologación escritorio / mobile — EN CURSO
- [x] Ambos escritorios: controles automáticos y evolución con mismas ventanas.
- [x] DEMO mobile: reemplazada fuente real escalada ×4 por inventario independiente V5; validaciones de 65 tickers, cuentas e importes.
- [x] DEMO mobile: pruebas de aislamiento, navegador, lectura y sintaxis.
- [x] Bersoch mobile: título de la aplicación corregido.
- [ ] Certificar visualmente mobile real y DEMO en dispositivos, incluida carga de inventario y estado offline.
- [x] DEMO mobile: exposición, custodia, evolución desde snapshots independientes, comparación patrimonial, simulación ficticia y resumen hablado.
- [ ] Alinear funcionalidades móviles avanzadas (el DEMO mobile dirige IA/Comparar/Simulador al escritorio independiente).

## Regla de precisión
Las cotizaciones DEMO son indicativas. Los históricos observados no se convierten en rendimiento financiero. En ETF, mostrar pocos componentes importantes y su cobertura total; todo peso no explicado queda explícito como **no desagregado**.

## Automatización de fuentes
Se evaluará después de revisar el desarrollo benchmark aportado por el usuario. No integrar cotizaciones o movimientos de otra cartera.

## Auditoría de pendientes — 14/11/2026

### Estado comprobado en repositorios
- [x] Las dos instancias de escritorio apuntan a identificadores de Google Sheets distintos (según `portfolio_config.py`). Esto verifica separación de configuración; no sustituye una auditoría de contenidos ni de credenciales del despliegue.
- [x] Pull requests Top 10 ARS fusionados: Bersoch escritorio #30, DEMO escritorio #28 y DEMO Mobile #4.
- [ ] Confirmar que la versión pública de cada escritorio coincide con el último commit y que los gráficos se renderizan correctamente. Las pruebas automatizadas no sustituyen esta inspección.
- [ ] Verificar completitud de cotizaciones y snapshots de Bersoch para 12 y 13/11/2026, incluyendo origen de datos, corte horario y conciliación del patrimonio total. No reconstruir cierres con FUT solamente.
- [ ] Determinar vigencia de los datos históricos DEMO y asegurar que los rankings mensuales muestren referencia válida o ausencia de datos, nunca variaciones inventadas.
- [ ] Auditar reconciliación entre feeds, inventarios, series históricas y totales por cuenta, en cada instancia por separado.
- [ ] Comprobar publicación de ambas versiones Mobile una vez restablecidos los créditos de Netlify; no confundir merge con deploy.
- [ ] Revisar alcance efectivo del Asesor IA técnico ya integrado (PR #28 Bersoch, #26 DEMO) antes de programar trabajo adicional de EMA/RSI y ventanas de cinco años.
- [ ] Revisar automatización de cargas, fallas y alertas por cierres faltantes, preservando la separación entre fuentes Bersoch y DEMO.

### Restricciones de trabajo
- No cargar cotizaciones ni snapshots supuestos; registrar fecha y fuente verificable.
- Conservar valores patrimoniales en USD, precios individuales ARS donde corresponda y Cash dentro del patrimonio total, pero excluido de curvas por tipo.
- Conservar colores por tipo: Cripto rojo; ETF amarillo; CEDEAR verde; Bonos azul; Acciones gris.
- No asumir que Netlify bloquea Streamlit; validar sus despliegues independientemente.

### Hallazgos de auditoría de datos (lectura del 14/11/2026)
- [ ] **Bloqueo de snapshot identificado:** `control_integridad_v2` señala una posición sin valor y estado `BLOQUEADO` en ambas bases. En `app_feed_v2`, ticker **LLY** tiene valor `-`, con indicación «Fetch fallo - usando ultimo valor de referencia». Verificar cotización válida y la ruta de fallback antes de intentar regenerar cierres.
- [ ] **Bersoch:** último cierre visible en `snapshot_series_v2`: 11/11/2026; faltan cierres observados de 12 y 13/11. FUT actual en feed: US$ 4.600 al 13/11.
- [ ] **DEMO:** `snapshot_series_v2` termina el 21/10/2026; sus cierres iniciales coinciden con Bersoch. Revisar procedencia y eliminar dependencia histórica de cartera real mediante reconstrucción documentada, no borrado indiscriminado. FUT DEMO figura US$ 6.850 al 15/10: no sustituir automáticamente por las valuaciones reales.

### Reparaciones verificadas y pendientes históricos — 14/11/2026
- [x] **LLY desbloqueado con cierre respaldado:** CEDEAR ARS 43.100 al 13/11/2026, plazo 24hs, fuente BYMA vía Cohen: https://www.cohen.com.ar/Bursatil/Especie/LLY/MERVAL/24hs. GoogleFinance sigue siendo primario; si falla se utiliza respaldo fechado de cotizaciones_manuales_v2.
- [x] Ambas bases muestran 0 posiciones sin valor y control_integridad_v2 = APTO. Esto NO certifica la vigencia de todos los demás precios.
- [x] Alerta de snapshot actualizada: avisa al pasar una rueda hábil sin cierre, ya no tolera 10 días bajo la etiqueta «al día».
- [x] Código candidato Apps Script reforzado con control previo obligatorio y prohibición de snapshot automático en fin de semana. Continúa PREPARADO/NO INSTALADO.
- [x] DEMO escritorio y DEMO Mobile no calculan Top 10 ARS con el historial_precios heredado de Bersoch: avisarán cuando falte serie independiente DEMO V5. Tests de aislamiento agregados.
- [ ] No reconstruir snapshots 12 y 13/11 con valuaciones parciales; exige cotizaciones fechadas de todas las posiciones y conciliación completa.
- [ ] Discrepancia histórica LLY: historial_precios registraba ARS 23.100 de forma constante hasta 11/11, mientras IOL informa un cierre 11/11 de ARS 42.800 y 13/11 de ARS 43.100. Investigar y conciliar historia íntegra antes de reescribir snapshots. Fuente: https://iol.invertironline.com/Titulo/DatosHistoricos?mercado=BCBA&simbolo=LLY .
- [ ] Reconstruir historial de precios DEMO propio V5, con fuente y fechas. No confundir valorizaciones ficticias estables con cotizaciones unitarias de mercado.
