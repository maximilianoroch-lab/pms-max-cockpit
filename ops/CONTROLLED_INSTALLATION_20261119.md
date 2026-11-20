# Instalación controlada de los cuatro productos

Estado: preparación local; **NO INSTALADO, NO AUTORIZADO PARA PUBLICAR**.
Identidad exclusiva: Max. Continuidad detallada en el maestro privado de Max.
Este archivo no contiene datos patrimoniales, secretos ni IDs de las bases.

## Candidatos remotos comprobados el 19/11/2026

| Producto | Repositorio | PR único | Head candidato |
|---|---|---|---|
| PMS Bersoch escritorio | maximilianoroch-lab/pms-max-cockpit | #45 | 08f6907be153edace455fd4daefadb6421fa3216 |
| PMS Bersoch Mobile | maximilianoroch-lab/PMS-Bersoch-mobile | #6 | ee9c2af915fb2d62a9123562d087582d8852ae9d |
| DEMO PMS Max escritorio | maximilianoroch-lab/Demo-PMS-Max | #31 | 49e2c65cad7f6a8bcead9ba44afd87d48276aca0 |
| DEMO PMS Max Mobile | maximilianoroch-lab/DEMO-PMSMax-mobile | #5 | 011fa03eb09a3284e63ad7a8656440a7a536d7a4 |

Los cuatro son drafts abiertos, no fusionados y mergeables al consultar.
Mergeable no equivale a instalado. Los PR individuales anteriores quedan
superados: no reabrirlos ni fusionarlos en serie. No crear PR paralelos.
Un merge puede producir otro SHA: registrar también el SHA resultante y el
efectivamente publicado, sin deducirlos del head candidato.

El handler preventivo `LegacySnapshotSafe.gs` y sus pruebas son una preparación
local posterior al head de #45, no parte del candidato remoto anterior.
Revisar e integrar ese delta en el MISMO candidato antes de aprobarlo.
La documentación y parche recuperable están en el maestro privado.

## Restricciones y evidencia Netlify

Capturas aportadas por Max el 19/11: saldo210; período15/11–14/12;
concurrencia0/1; ambos sitios móviles muestran `Builds are stopped` y
`Trigger deploy` deshabilitado. Es evidencia de capturas, no acceso admin.

- Reserva mínima100. Diferencia110 es margen aritmético, no permiso de gasto.
- Consultar a Max ANTES de cualquier acción que consuma créditos Netlify.
- Mantener builds automáticos detenidos. Ningún deploy exploratorio o preview.
- No prometer costo cero para subir/promover un artefacto existente: verificar
  la modalidad, plan y costo efectivo antes de incluirlo en la autorización.
- No habilitar auto-merge, builds, webhooks ni publicación por push para probar.

## Bloqueo de seguridad de la base personal

No quitar el acceso público hasta migrar y probar TODOS los consumidores.
La autenticación administrativa de Netlify no protege por sí sola los datos
que las aplicaciones obtienen de una hoja pública.

Inventario comprobado en el escritorio candidato: `data.py:load_all_data`
consulta GViz para todos los feeds; `app.py:_load_monthly_type_values`
consulta la serie mensual; `app.py:_manual_history_sources` consulta
operaciones e inventario. La migración debe cubrir las tres rutas, incluida
la lectura de dos tablas en la última.

Inventario Mobile comprobado en el head exacto #6: `index.html:getCSV` usa
GViz desde el navegador para11 lecturas: posiciones/home/banner en app_feed_v2,
tipo, exposición, resumen/detalle de custodia, snapshots, caja, serie mensual
e historial_precios. `saveCache/loadCache` persiste el lote en localStorage
sin vencimiento por antigüedad; la fecha se valida pero no hay TTL máximo.
El código del asesor en sessionStorage protege solo el asesor, no esos feeds.
`sw.js` omite interceptar docs.google.com; esa excepción tampoco autentica
lecturas ni borra localStorage. La migración privada debe cubrir estas11
lecturas, controlar retención offline y verificar otros consumidores externos
antes de revocar permisos. Este documento no implementa dicha migración.

Preparar transporte autenticado del lado servidor, autenticación de usuario,
configuración privada y permisos mínimos; ningún secreto en JS descargable.
En modo privado no permitir fallback silencioso a GViz público. Probar
acceso autorizado, rechazo de anónimos, cierre de sesión y caché offline.
El navegador personal puede conservar datos offline: revocar acceso a la hoja
no borra esas copias. Tratar esa retención expresamente antes de habilitarla.
DEMO debe usar solo su base e históricos independientes; no copiar datos
personales para tests ni usar controles heredados como validación V5.

## Respaldos requeridos antes de pedir publicación

1. Sheets bajo Max: verificar copia, permisos privados, fórmulas y rangos
   afectados. Las copias con fórmulas activas no son valuaciones congeladas.
2. Apps Script: exportar archivos reales y manifest; guardar configuración
   privada, propietario, zona horaria, IDs/handlers/horarios de activadores.
   Los horarios de última ejecución no prueban programación exacta.
3. Netlify: registrar deploy publicado, SHA, artefacto, functions, variables
   por nombre/ámbito sin exponer valores y posibilidad real de rollback.
4. Streamlit: registrar repositorio, rama, entrypoint, runtime, SHA efectivo,
   configuración privada y método de volver a versión anterior.
5. Verificar quién puede restaurar y cómo se hará. Un backup sin prueba de
   lectura/consistencia no acredita restauración integral.

## Paquete único de autorización — todavía incompleto

Antes de solicitar aprobación, completar esta tabla con evidencia vigente.
No pedir un permiso genérico con costos, SHAs o rollback desconocidos.

| Requisito | Estado al corte |
|---|---|
| Cuatro candidatos exactos y separación de repositorios | comprobados en GitHub |
| Corrección legacy y16 pruebas offline | preparada local; no instalada |
| Saldo y builds detenidos | capturas de Max19/11 |
| Código Apps Script completo, manifest y respaldo | incompleto |
| Horarios/permisos/errores reales de activadores | incompleto |
| Lectura privada integral y protección de apps personales | pendiente |
| SHA efectivo y rollback de ambos Streamlit | pendiente |
| Artefactos/rollback/costo exacto de ambos Netlify | pendiente |
| Prueba aislada de instalación con configuración real | pendiente |

La solicitud final debe enumerar por producto: SHA final, cambios concretos,
base y variables verificadas privadamente, automatizaciones a conservar o
cambiar, riesgos, reversión, crédito estimado y tope de gasto autorizado.
Autorizar publicación no autoriza reparar históricos o movimientos.
Activadores requieren autorización específica y lista exacta, sin duplicados.

## Ejecución posterior a la aprobación

Validar nuevamente los heads y evidencia de saldo antes de empezar. Instalar
solo los artefactos aprobados, uno por producto, usando la modalidad autorizada.
Detener ante SHA distinto, coste inesperado, fallo de integridad o rollback
no disponible. No reintentar builds consumiendo créditos por iniciativa propia.

Verificar en cada producto navegación, dos rankings cuando la cobertura de
datos lo permita, cálculos y sus etiquetas, estados vacíos/errores, identidad
personal/DEMO, functions sin llamadas pagas no aprobadas y comportamiento móvil
online/offline. Registrar SHA realmente publicado, no solo HTTP200 o CI verde.
No habilitar componentes ETF sujetos a restricciones de licencia.

V3 guarda observaciones separadas, no cierre certificado. El nuevo handler
legacy detecta estados parciales pero no hace atómicas dos escrituras. No
reparar filas ni completar fechas ausentes automáticamente.

## Reversión

- Apps: volver al artefacto o SHA anterior previamente identificado y verificar
  las cuatro URLs. Cualquier gasto de rollback debe estar contemplado en el
  permiso; si no lo está, consultar antes de consumir créditos.
- Apps Script: desactivar el handler nuevo y restaurar código/configuración y
  activador anterior según el plan específicamente aprobado.
- Datos: conservar registros producidos y auditar; no borrar/compensar cierres
  ni restaurar encima de movimientos posteriores sin aprobación patrimonial.
- Acceso: no reabrir públicamente la base personal como rollback automático.
  Cualquier cambio de seguridad necesita decisión expresa, no improvisación.

No se declara completado el proyecto hasta verificar producción y registrar
el PUNTO EXACTO DE REANUDACIÓN en el maestro.
