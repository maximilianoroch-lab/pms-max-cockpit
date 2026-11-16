# WORK_HANDOFF — Maestro de Inversiones (corte 15/11/2026)

## Instrucción fundamental

**Este documento es el contrato de traspaso de Chat a Work.** Antes de escribir o desplegar, Work debe leer este archivo y los cuatro PR, revisar el estado LIVE de cada servicio, contrastar SHAs con la tabla, y registrar cualquier divergencia. No reconstruir decisiones leyendo cientos de chats. No confundir `CI success` con instalación, publicación, salud de producción ni certificación de datos.

**Objetivo:** PMS Bersoch personal (escritorio/móvil) y DEMO PMS Max (escritorio/móvil), completamente aislados. El usuario prefiere automatizar la interacción con interfaces en Work; evitar pedirle tareas mecánicas de mouse. Reservar sus acciones para permisos, confirmación de fechas de operaciones y aprobaciones que modifiquen producción.

## Cuatro únicos PR abiertos y SHAs candidatos

| Producto | Repositorio | PR | SHA candidato | CI verificado en Chat | Base |
|---|---|---:|---|---|---|
| Bersoch escritorio | `maximilianoroch-lab/pms-max-cockpit` | [#45](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/45) | `ca305a351678c32ec092666d6777311fd5e81e57` | 14/14 | main |
| DEMO escritorio | `maximilianoroch-lab/Demo-PMS-Max` | [#31](https://github.com/maximilianoroch-lab/Demo-PMS-Max/pull/31) | `b6e6f7d31690a6961f1b498eb5938523c185dd42` | 5/5 | main |
| Bersoch móvil | `maximilianoroch-lab/PMS-Bersoch-mobile` | [#6](https://github.com/maximilianoroch-lab/PMS-Bersoch-mobile/pull/6) | `a96f87baed9ca77459bc1a736d85791139879e59` | 1/1 | main |
| DEMO móvil | `maximilianoroch-lab/DEMO-PMSMax-mobile` | [#5](https://github.com/maximilianoroch-lab/DEMO-PMSMax-mobile/pull/5) | `011fa03eb09a3284e63ad7a8656440a7a536d7a4` | 1/1 | main |

**17 PR anteriores fueron cerrados como superados, NO fusionados**: Bersoch escritorio #31–#44, DEMO escritorio #29–#30 y Bersoch Mobile #5. El PR antiguo de bonos #3 también fue cerrado antes, reemplazado por el módulo de solo lectura incluido en #45. Sus ramas y discusiones permanecen para auditoría. Solo los 4 PR de la tabla son candidatos actuales. No volver a fusionar candidatos anteriores en secuencia.

Verificar nuevamente SHAs, cambios respecto de main, CI y estado de PR al iniciar Work. Una aprobación de GitHub no garantiza permiso administrativo ni que la app publicada corresponda a ese SHA.

## Netlify: limitación presupuestaria obligatoria

El usuario informó **210 créditos disponibles para todo el mes** (estado comunicado el 15/11/2026) y confirmó **Stopped builds en ambos sitios móviles**. Son datos comunicados por el usuario; revisar el panel al comenzar Work para comprobar estado actualizado.

- Mantener **Stopped builds** hasta listo el lote completo. No activar builds automáticos por cada push o merge. Evitar previews, tests con funciones y otras acciones que consuman uso sin beneficio; incluso sin builds puede haber consumo de tráfico/funciones.
- Política presupuestaria propuesta, no factura: preservar al menos **100 créditos de reserva**, planificar las dos publicaciones móviles juntas, hacer antes validación de código sin Netlify, y revisar consumo después de CADA deploy.
- No asumir una tarifa de publicación fija sin leer las condiciones y el medidor vigente del plan. No activar auto-recarga. Registrar saldo **antes** y **después** de cada acción y detener el despliegue si amenaza la reserva.
- No desplegar para ver si funciona: verificar localmente/CI y usar una sola publicación final controlada por sitio cuando esté lista.
- La app de escritorio Streamlit puede publicar automáticamente al fusionar main: inspeccionar configuración Streamlit Cloud antes de cualquier merge.

## Bases separadas y preparación ejecutada

- **Base PMS Bersoch**, Sheet ID `18qu9LXo55qQZq4oEAq42u_DKaI7e9lZL_PkfUZiu0T0`. Última verificación Chat: 66 posiciones, control_integridad_v2!D6 = APTO, cifras conciliadas a nivel resumen; esto **NO certifica precios**.
- **Base DEMO PMS Max**, Sheet ID `1xzmw5US1z9CGj0eYdGYS2_FfpSzklGyOYODCJ6vvlcY`, 65 instrumentos ficticios; jamás copiar historia ni posiciones personales a DEMO.
- El 15/11 se **crearon directamente** en la base personal, sin tocar posiciones ni históricos:
  1. `observaciones_intradiarias_v3`, con 12 encabezados y sin registros de captura.
  2. `feriados_mercado_v3`, con 17 fechas sin negociación BYMA 2026 y fuente descriptiva.
- Se releyeron ambas y el control de integridad. Los activadores Apps Script **NO** fueron inspeccionados ni instalados por Chat. Su existencia/estado es desconocido. Hay código legacy en `APPS_SCRIPT_V2` etiquetado «preparado / no instalado» que NO acredita ausencia de triggers reales.
- Las capturas V3 aprobadas en simulación usan funciones `pmsV3_1100`, `pmsV3_1400`, `pmsV3_1700`; observaciones intradiarias son `OBSERVADO_NO_CERTIFICADO` o `OBSERVADO_BYMA_CERRADO_NO_CERTIFICADO`. **La foto de las 17:00 NO es cierre BYMA**; desde 02/11 se negocian acciones/CEDEAR hasta las 18:00.
- Los seriales Google Sheets de «Fecha actualización» se etiquetan NO MERCADO. No tratarlos como timestamp verdadero de cotización. V3 se niega a publicar valores como cierres certificados.
- Calendario BYMA solo modela BYMA, no EEUU/cripto. Los días 09–10/11 no hubo rueda BYMA pero puede haber cambios patrimoniales multibolsa.

## Trabajo a realizar por Work en orden y condiciones

1. **Inspección sin escrituras:** comprobar las cuatro apps publicadas, panel de Netlify/Streamlit, commit desplegado, estado y costo, ambientes/secrets (solo presencia, NO mostrar valores), backups/rollback, permisos y triggers Apps Script. Informar hallazgos divergentes sin alterar configuración.
2. **Respaldo antes de cambiar producción:** crear copias recuperables de las dos Sheets, código Apps Script y configuración de activadores, referencias de deploy y SHAs vigentes. Mantener DEMO separada. Nunca subir archivos privados a repositorios públicos.
3. **Validación de integridad:** revisar 66 posiciones personales y 65 DEMO, filas de historial/snapshot, controles de caja/custodia, bitácora de fuentes, lógica de valoración del patrimonio. El código puede aprobar CI con datos stale.
4. **Release candidate:** los cuatro PR de arriba son la única referencia. Confirmar diffs sin cambios de secretos o fuentes personales en DEMO; probar funcionalidades, offline, rutas, taxonomía de cinco tipos (GLD es ETF), asesor IA seguro y caducidad del caché.
5. **Autorización de instalación:** pedir autorización concreta para merge/publicación y para activadores Apps Script si el usuario no la ha dado explícitamente para el cambio identificado. No interpretar «A» como permiso para reescribir patrimonio ni activar disparadores sin auditoría.
6. **Despliegue controlado:** fusionar SOLO los cuatro PR candidatos aprobados (y verificaciones posteriores) en el orden que permita conservar rollback y evitar cambios involuntarios de Streamlit. Publicar cada móvil UNA vez cuando validado y revisar consumo. No reactivar builds automáticos sin autorización.
7. **Apps Script V3:** examinar activadores existentes (posibles 11/14/17 y legado). Hacer prueba aislada controlada y verificar idempotencia; nunca duplicar triggers ni promover capturas a historial certificado. Captura de lunes a viernes y marca BYMA cerrado en las fechas del calendario. Probar rechazo de datos faltantes y no modificación de historia.
8. **Certificación post-deploy:** identificar SHAs de cada app LIVE; pruebas de navegación y datos Bersoch/DEMO separados, holdings/cash, gráficos 5 tipos, móvil online/offline, acceso seguro al asesor, fecha de fuente, fallas HTTP/UX. Registrar evidencia y rollback.
9. **Datos históricos:** abordar 12/13 noviembre, LLY y movimientos SOLO después de obtener evidencia homogénea. No usar trigger V3 para inventar cierres retroactivos.
10. **Cierre:** documentar estado LIVE, SHA/URL, datos no conciliados, pruebas, costo neto de Netlify, backups y cómo revertir; no marcar «terminado» cuando haya bloqueos reales.

## Bloqueos patrimoniales — NO resolver por inferencia

- **Cierres 12/13 noviembre:** no hay cobertura certificada de posiciones, cotizaciones por ticker/fecha/plaza/horario, FX y caja. Un número observado hoy no sirve para rellenar un cierre histórico.
- **LLY:** `historial_precios` tuvo 19 observaciones 08/10–11/11 con ARS 23.100 repetido; indicio de precio viejo/fallback. 09–10/11 BYMA cerrado. Deben confirmarse precios por fecha, plazo/serie/CEDEAR, cantidad e identificador antes de cambiar 19 filas.
- **Cuatro transacciones recientes:** venta MSFT en Adcap; compra GOOGL en Galicia; depósito Galicia; retiro Adcap. Falta fecha efectiva verificada y conciliación de los comprobantes/flujo interno-externo. No inventar fechas, importes, cash, movimientos, ni registrar dos veces. No reproducir importes personales aquí.
- **ETF:** módulo de solapamiento y política de materialidad 1% identificado / 2% sin desagregar / 30 días de fuente son **propuestos, NO activados**. El catálogo de siete fuentes en #45 NO contiene holdings ni pesos de terceros por revisión pendiente de derechos de redistribución. No volver a insertar un CSV de holdings de iShares sin licencia adecuada. La propuesta no es una señal de inversión.
- **DEMO historia:** sin serie independiente documentada por ticker, fecha y divisa, los rankings históricos y movers se mantienen bloqueados. No copiar el historial real Bersoch.
- **Seguridad de funciones:** nunca copiar OPENAI_API_KEY ni ADVISOR_ACCESS_CODE en GitHub o frontend; inspeccionar variables solo por presencia y evaluar rate limits/uso antes de habilitar un asesor de pago.

## Hitos de comunicación

Work debería producir al inicio un diagnóstico exacto de accesos y disparadores, luego un plan de publicación con costo máximo verificable y SHA por producto. Reportar avances al completar cada bloque; solicitar SOLO la autorización necesaria, sin convertir al usuario en operador manual.

Este documento y los cuatro PR son la referencia técnica. No borra ni transforma datos privados ni sustituye una auditoría financiera.
