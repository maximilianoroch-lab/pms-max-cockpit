# Lectura privada de Sheets — escritorio personal — NO INSTALADO

El adaptador `private_sheet_reader.py` usa Sheets API v4 con scope
`spreadsheets.readonly`, cuenta de servicio del lado servidor y base/pestañas
permitidas explícitamente. No cambia permisos, crea cuentas ni escribe datos.
Las tres rutas de la UI pasan por `read_sheet_csv`, incluido historial manual.

Configuración prevista, exclusivamente en secrets del hosting:

```toml
[PMS_SHEETS]
mode = "private"
spreadsheet_id = "ID_PERSONAL_VERIFICADO_PRIVADAMENTE"

[PMS_GOOGLE_SERVICE_ACCOUNT]
type = "service_account"
client_email = "CUENTA_DE_SERVICIO_APROBADA"
private_key = "CLAVE_PRIVADA_SOLO_EN_HOSTING"
token_uri = "https://oauth2.googleapis.com/token"
```

No subir valores reales a GitHub o al chat. Cuenta lectora solo para base
personal tras aprobación explícita; sin delegación de dominio. Revisar permisos
de esa cuenta y la API habilitada antes de probar contra staging privado.
No usar cuenta, base o credenciales DEMO para esa prueba.

Ausencia de modo privado conserva el transporte público legacy para no romper
la versión existente por preparar el código. Configurar private sin credenciales
válidas bloquea: no hay fallback a GViz. No habilitar hasta que staging confirme
equivalencia de encabezados, formatos numéricos, fechas y rangos con GViz; Sheets
API y GViz pueden representar fórmulas/encabezados de manera diferente.

Actualización19/11: personal_user_access.py agrega ingreso Google OIDC nativo de Streamlit y allowlist ANTES de cualquier lectura o caché patrimonial. Preparado y probado localmente; no certifica OAuth real. Configuración adicional requerida en secretos del hosting:

```toml
[PMS_ACCESS]
allowed_emails = ["USUARIO_AUTORIZADO"]
# allowed_subjects = ["SUB_GOOGLE_VERIFICADO"]
[auth]
redirect_uri = "https://HOST_PERSONAL/oauth2callback"
cookie_secret = "SECRETO_GENERADO_FUERA_DEL_CHAT"
[auth.google]
client_id = "CLIENTE_OAUTH_APROBADO"
client_secret = "SECRETO_SOLO_EN_HOSTING"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

La sesión exige email verificado, issuer Google, subject, allowlist y expiración/antigüedad válidas. Configuración privada incompleta o tercero bloquea. Cerrar sesión usa st.logout. Falta alta/configuración administrativa del cliente, consentimiento, credenciales lectoras y prueba real de acceso permitido/denegado. Mobile tiene preparación separada en su candidato, aún no instalada. Revisar consumidores externos y ambos productos antes de retirar acceso público. No habilitar por este documento.

No se generaron credenciales ni compartió una base. No se desplegó ni consumió
Netlify. Rollback de código no implica reabrir públicamente la hoja.

Referencias oficiales consultadas19/11/2026:
- https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/get
- https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.service_account.html
