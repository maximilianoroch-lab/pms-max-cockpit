# Instalación conjunta PMS Bersoch + DEMO PMS Max — plan de liberación

> **SUPERADO COMO INSTRUCCIÓN DE INSTALACIÓN (19/11/2026).**
> Conservar como antecedente; no ejecutar su secuencia de PR individuales.
> Usar [CONTROLLED_INSTALLATION_20261119.md](CONTROLLED_INSTALLATION_20261119.md)
> con los cuatro candidatos consolidados. Publicación, gasto y activadores siguen sin autorizar.

**Estado:** borrador de integración, NO instalado. Fecha de corte: 15/11/2026. Este plan abarca los cuatro productos: Bersoch escritorio y Mobile, DEMO escritorio y Mobile.

## Inventario de candidatos

| Área | Repo | PR | Prueba simulada | Dependencia de publicación |
|---|---|---|---|---|
| Capturas 11/14/17 | Bersoch escritorio | #31 | Tests Apps Script + calidad | Inspección Apps Script, tres disparadores, calendario, calidad por ticker |
| Monitor de frescura | Bersoch escritorio | #32 | Tests Python + calendario BYMA 2026 | Definir calendario multibolsa y activar CSV solo con criterio acordado |
| Auditoría LLY histórica | Bersoch escritorio | #33 | Tests + calidad | Precio homogéneo y archivo histórico verificable |
| HTTP sin falsos verdes | Bersoch escritorio | #34 | Tests + calidad | Comprobación real de Streamlit y Netlify |
| Cierres 12/13 y fechas BYMA cerradas | Bersoch escritorio | #35 | Tests + calidad | Tenencias y cotizaciones fechadas; conciliar caja/FX y fechas 9/10 |
| Bonos — diagnóstico seguro | Bersoch escritorio | #36 | Tests + calidad | Fuente, unidad, modalidad, y segunda cotización; no habilitar escrituras |
| Movimientos no conciliados | Bersoch escritorio | #37 | Tests + calidad | Fechas de cada transacción, comprobantes y carácter de flujo externo |
| DEMO historia precios independiente | DEMO escritorio | #29 | Tests + aislamiento | Proveedor fechado y universo ficticio independiente |
| Bersoch Mobile caché íntegra | Bersoch Mobile | #5 | Playwright + advisor | Publicación y test en dispositivo real |
| DEMO Mobile offline validado | DEMO Mobile | #5 | Playwright + advisor | Publicación y test en dispositivo real |

**El PR antiguo Bersoch #3 quedó cerrado como obsoleto/superado por #36.** No reabrirlo ni instalar su código de escritura.

## Reglas de seguridad

- **No fusionar los PR como si fueran una transacción única.** Cada uno tiene dependencias y pruebas independientes. Leer diffs y hacer una integración técnica conjunta en una rama de release, ejecutando todos los tests antes de un merge.
- **No activar Apps Script todavía.** Inspeccionar disparadores preexistentes, hacer copia de código y de pestañas afectadas, verificar permisos y ejecutar diagnóstico sin escritura primero.
- **No crear cierres del 12/13 desde cotizaciones de fechas posteriores.** El preflight #35 es solo lectura. Reconciliar cantidades, horarios, cash, tipo de cambio, operativa, ratios y unidad de precios.
- **No confundir calendario BYMA con calendario completo de cartera.** 09/11 y 10/11 no tuvieron rueda BYMA, pero US y cripto pueden variar. El CSV en #32 es BYMA solamente y no resuelve activos multibolsa.
- **Nunca usar la base real Bersoch para reconstruir la historia de la DEMO.** El gate #29 solo acepta fuente externa histórica con origen documentado; hasta entonces mantener rankings bloqueados.
- **No dar por certificado un despliegue porque CI terminó verde.** Registrar URL, commit desplegado y pruebas reales de UI, datos y móvil. Streamlit puede no renderizarse en el entorno GitHub.
- **No publicar datos patrimoniales ni secretos en artefactos GitHub.** Los tests solo contienen fixtures ficticios.

## Secuencia de integración (no ejecutar sin autorización de instalación)

1. Congelar versión actual y respaldar código, pestañas y cron de cuatro productos.
2. Resolver primero validadores sin escritura: #33, #34, #35, #36, #37 y #29. Ejecutar regresiones y verificar que cada módulo solo lee datos.
3. Revisar y conciliar las dependencias entre #31 y #32: el capturador V3 requiere pestaña de feriados, el monitor V2 un CSV; una convención BYMA no basta para cripto/mercados externos. Evitar dos sistemas independientes de feriados contradictorios.
4. Fusionar y desplegar mejoras móviles #5/#5 con pruebas en navegador y dispositivos, manteniendo claro el estado de datos guardados.
5. Promover únicamente código validado en una rama de release por repositorio; ejecutar matrices de calidad, aislamiento, seguridad, integridad y pruebas E2E.
6. Para habilitar captures 11/14/17: confirmar base activa, inspeccionar activadores existentes, autorizar instalación de tres funciones **sin duplicados**, correr captura staging, garantizar append-only, probar alertas de errores.
7. Comprobar snapshots posteriores; conservar originales y auditoría del primer cierre validado. Backfill histórico por proceso separado.
8. Verificar versiones en Streamlit Cloud y Netlify, anotar SHA efectivamente desplegado, estado de publicación, funcionamiento del asesor IA, vistas, precios y desconexión.
9. Registrar rollback por cada producto y un control de salud posterior. Ninguna modificación de patrimonio sin reconciliación previa.

## Bloqueos que sí requieren algo externo

1. **Apps Script:** acceso a activadores/logs y autorización para instalar funciones; sin ello no puede probarse ejecución real.
2. **Operaciones recientes:** falta fecha efectiva y verificación de asientos en broker/Sheet; no suponer día por chat.
3. **12/13 noviembre y LLY:** falta fuente uniforme, per-ticker y por fecha para completar y conciliar cierres. No imputar históricos.
4. **DEMO:** no se dispone todavía de una fuente independiente por activo, fecha, divisa y plaza para historial de precios de mercado.
5. **Publicación:** se requiere acceso a Streamlit Cloud/Netlify o comprobación de URL y SHA desplegado para certificar la funcionalidad.
6. **ETF:** faltan principales tenencias fechadas con fuentes; una estimación de cobertura no implica composición completa.

## Condición de salida

El proyecto **NO** se declara «terminado» porque los tests simulados estén verdes. El estado correcto es «borradores técnicos preparados; pendientes de datos/acceso/instalación». El paquete de release estará listo para instalar solo cuando los bloqueos de código e integración estén resueltos; despliegue y certificación requieren validación posterior.


## Revisión cruzada ejecutada posteriormente (15/11/2026)

- GitHub confirmó como **exitosos** los controles individuales de los ocho borradores Bersoch escritorio #31–#38 (en la revisión previa al cambio de calendario).
- También pasaron las pruebas individuales de DEMO escritorio #29 y los borradores móviles #5/#5.
- Se identificó y corrigió en #31 una incompatibilidad con el calendario BYMA: anteriormente se descartaba la captura de toda la cartera en un feriado argentino; ahora se conserva la observación multibolsa con etiqueta `OBSERVADO_BYMA_CERRADO_NO_CERTIFICADO`, sin convertirla en cierre de BYMA.
- El PR #31 tiene una prueba específica de esa condición. **Antes de integrar**, volver a comprobar que su último commit y los controles generales siguen verdes.
- **Precisión:** que todos los PR sean individualmente fusionables y hayan aprobado CI **no demuestra** que una rama con todos simultáneamente no tenga conflictos o fallos de contrato; sigue pendiente la prueba integrada de instalación.
- Las dos versiones móviles y la DEMO escritorio también mostraron sus controles individuales en verde durante la verificación de este corte. Sigue faltando comprobar el SHA desplegado en Netlify/Streamlit.


## Licencias de datos de ETF — BLOQUEO DE PUBLICACIÓN (15/11/2026)

El repositorio es **público**. La documentación de BlackRock/iShares restringe el uso y redistribución de las descargas de holdings. El PR #43 fue reescrito para conservar solamente metadatos de fuente y fecha; su rama actual **no tiene `etf_top_holdings.csv`**. El motor de look-through continúa probado pero no debe usar composiciones de terceros en el dashboard hasta confirmar permisos adecuados o datos con licencia reutilizable.

El catálogo `ops/etf_sources_registry.csv` contiene URL, emisor y fecha de siete ETF como referencias, no posiciones ni porcentajes. GLD es exposición a oro, no se debe modelar como cesta accionaria. La fecha de una fuente oficial tampoco equivale por sí sola a autorización para republicar.
