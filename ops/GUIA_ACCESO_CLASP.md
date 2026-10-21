# Acceso seguro a Apps Script desde GitHub (preparación, NO activar)

Proyecto identificado por el propietario. **No incorporar identificadores, tokens OAuth ni archivos `.clasprc.json` al repositorio**.

## Secuencia segura
1. Google: habilitar la **Apps Script API** en https://script.google.com/home/usersettings (requiere la cuenta propietaria).
2. Autenticación de `clasp`: Google requiere consentimiento OAuth del propietario. Se debe realizar en su sesión de confianza, NO enviando el archivo `.clasprc.json` al chat.
3. Configurar el identificador del script en el secreto GitHub `CLASP_JSON` y el token OAuth en `CLASPRC_JSON` **solo dentro de GitHub Actions secrets**. Los secretos contienen capacidades de edición del script: mínimo privilegio.
4. Hacer `clasp pull` de todos los archivos existentes y respaldar antes de cualquier `push`; el proyecto ya contiene automatizaciones MEP y snapshots y **no debe sobrescribirse con un solo Bonos.gs**.
5. Revisión y pruebas de diagnóstico no escrituras; publicar a producción únicamente con aprobación explícita y recuperación posible.

La documentación oficial sobre CI/CD: https://developers.google.com/apps-script/guides/clasp

Estado: solo documentación; **ninguna credencial enlazada; ningún despliegue habilitado**.
