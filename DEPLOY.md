# Deploy PMS Max Cockpit

1. Crear repo privado en GitHub, por ejemplo `pms-max-cockpit`.
2. Subir estos archivos a la raíz.
3. En Streamlit Community Cloud: Create app → repo → `app.py`.
4. En Settings > Secrets:
```toml
OPENAI_API_KEY = "..."
# OPENAI_MODEL = "gpt-5.6"
```
5. Reiniciar la app.

No mezclar datos/configuración de PMS Grupo ni terceros en esta instancia.
El Dashboard funciona sin API key. El Asesor IA y las consultas externas requieren API key.
