# Instalación conjunta — PMS Bersoch y DEMO PMS Max

> **SUPERADO COMO INSTRUCCIÓN DE INSTALACIÓN (19/11/2026).**
> Este documento es antecedente histórico. No fusionar sus PR individuales.
> La secuencia vigente y los cuatro candidatos consolidados están en
> [CONTROLLED_INSTALLATION_20261119.md](CONTROLLED_INSTALLATION_20261119.md).
> Ninguna aprobación histórica de CI autoriza publicar, gastar créditos o instalar activadores.

**Estado: PREPARADO PARA REVISIÓN, NO INSTALADO.** Control de cambios del 15/11/2026. La aprobación de CI solo prueba código simulado; no acredita datos bursátiles, Apps Script, sincronización de Google Sheets, ni publicación de las cuatro aplicaciones.

## Borradores vigentes

| Producto | PR | Alcance | Prerrequisito externo |
| --- | --- | --- | --- |
| PMS Bersoch Desktop | [#31](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/31) | Capturas observadas 11/14/17, separadas del cierre certificado | Inspeccionar Apps Script, permisos y fuentes fechadas; no duplicar triggers |
| PMS Bersoch Desktop | [#32](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/32) | Monitor con calendario BYMA 2026 | Elegir calendario por mercado y aprobar configuración |
| PMS Bersoch Desktop | [#33](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/33) | Auditoría LLY de solo lectura | Precios históricos, plaza y plazo homogéneos |
| PMS Bersoch Desktop | [#34](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/34) | Diagnóstico HTTP que no da falsos verdes | Confirmación visual del deployment |
| PMS Bersoch Desktop | [#35](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/35) | Cobertura de tenencias y cotizaciones 12–13/11, plus fechas BYMA cerradas | Exportación fechada, FX, caja y movimientos conciliados |
| PMS Bersoch Desktop | [#36](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/36) | Diagnóstico bonos IOL **sin escritura** | Confirmar fuente, unidad ARS por 100 VN, divisa y settlement |
| DEMO PMS Max Desktop | [#29](https://github.com/maximilianoroch-lab/Demo-PMS-Max/pull/29) | Validador de precios históricos independientes | Cotizaciones por ticker/fecha, procedencia DEMO |
| PMS Bersoch Mobile | [#5](https://github.com/maximilianoroch-lab/PMS-Bersoch-mobile/pull/5) | Caché offline validada | Certificación navegador y publicación Netlify |
| DEMO PMS Max Mobile | [#5](https://github.com/maximilianoroch-lab/DEMO-PMSMax-mobile/pull/5) | Caché offline de inventario ficticio | Certificación navegador y publicación Netlify |

El antiguo [PR #3](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/3) de bonos fue cerrado por estar superado: **no instalarlo**. PRs abiertos en ramas distintas no pueden asumirse integrados entre sí. Realizar revisión de conflictos, pruebas globales y merge en orden controlado.

## Orden propuesto para la sesión de instalación

1. **Backup verificable** de ambas Google Sheets y versiones de producción de las cuatro apps. Registrar IDs, hashes/fechas y procedimiento de rollback. No copiar posiciones reales a repositorio DEMO.
2. **Auditoría de movimientos recientes:** cuatro movimientos comunicados por el titular requieren conciliación de fecha efectiva, cuenta, efectivo y comprobantes. NO poner importes privados ni operaciones identificables en un repositorio público; mantener el detalle únicamente en la base privada autorizada. No imputar por deducción.
3. **Cotizaciones:** verificar fuente/plaza/plazo, fechas reales por ticker, FX, bonos y FUT; los campos `Fecha dato` de recálculo de Sheets no son prueba de cierre bursátil.
4. **Históricos:** auditar 9–10/11 como días sin negociación BYMA pero posibles movimientos de otros mercados; completar 12–13/11 solo con posiciones y precios fechados conciliados, sin sobrescribir originales.
5. **Apps Script:** listar activadores existentes antes de agregar, validar permisos, zona horaria America/Argentina/Buenos_Aires, seis bonos sin escritura, manejo de feriados específicos por plaza, alertas de fallos, monitoreo y mecanismo de desactivación. No ejecutar capturas nuevas etiquetadas como “CIERRE VERIFICADO” sin evidencia.
6. **Pruebas end-to-end staging:** verificación de cantidad por ticker/custodio, cuentas, sumatorias USD, de duplicados y de integridad histórica. Probar capturas 11/14/17 en fechas controladas, un rerun idéntico y una captura previa incompleta. Validar registros y logs.
7. **Merge controlado + publicación:** fusionar borradores no conflictivos, verificar CI sobre el commit integrado, publicar dos escritorios y dos móviles. Confirmar commit real desplegado, nombre correcto, datos correctos, modo offline, gráficos y funciones. Un HTTP 200 no certifica app Streamlit.
8. **Postinstalación:** observar el primer ciclo bursátil, comprobar que se generaron las tres observaciones y alerta de falta; documentar rollback y confirmar que ningún precio falso se promovió a historia.

## Restricciones no negociables

- **Bersoch ≠ DEMO:** bases e históricos diferentes; la DEMO tiene 65 activos ficticios (a la revisión), Bersoch 66 posiciones reales; no importar historia privada ni cuentas.
- No reescribir cierres, flujos, tenencias, TCs ni instrumentos sin conciliación y autorización específica.
- La validación `APTO` no certifica frescura de precios.
- No instalar capturador V3 y calendario BYMA en forma inconexa: el modelo debe contemplar mercados de EE.UU., BYMA y cripto; BYMA cerrado no significa cartera congelada.
- Versionar la lista definitiva de tareas y los bloqueos con evidencia y responsable; no reabrir trabajo ya aprobado salvo regresiones.

## Estado de bloqueos

**Bloqueos patrimoniales:** fecha y conciliación de movimientos comunicados por el titular; historia por activo de 12/13; LLY y precio de bonos/FX; DEMO histórica independiente.

**Bloqueos operativos:** inspección y activación Apps Script, fuentes e infraestructura Netlify/Streamlit (confirmación de publicación), revisión manual de aplicación en dispositivos.

**Trabajos autónomos posibles:** mantener suites de prueba, código de lectura, monitoreo, revisión de compatibilidad y documentación. Cada PR en borrador es reversible y no cambia producción.
