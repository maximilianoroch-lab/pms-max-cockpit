"""Optional server-side Sheets reader. Preparation only; no permission changes.

This authenticates the server to Sheets, NOT the visitor to the application.
Hosting/user access control must be verified separately before production use.
"""
import csv
from io import StringIO
from urllib.parse import quote

READ_SCOPE = 'https://www.googleapis.com/auth/spreadsheets.readonly'
TOKEN_URI = 'https://oauth2.googleapis.com/token'


class PrivateSheetError(RuntimeError):
    pass


class PrivateSheetReader:
    def __init__(self, spreadsheet_id, allowed_sheets, session):
        if not spreadsheet_id or not isinstance(spreadsheet_id, str):
            raise PrivateSheetError('Falta base privada configurada')
        self.spreadsheet_id = spreadsheet_id
        self.allowed_sheets = frozenset(allowed_sheets)
        self.session = session

    def __call__(self, spreadsheet_id, sheet, cell_range=None):
        if spreadsheet_id != self.spreadsheet_id or sheet not in self.allowed_sheets:
            raise PrivateSheetError('Lectura fuera de la base o pestañas autorizadas')
        # Sheet name is quoted, including embedded apostrophes, not evaluated.
        a1 = "'" + sheet.replace("'", "''") + "'"
        if cell_range:
            import re
            if not re.fullmatch(r'[A-Z]+[1-9][0-9]*:[A-Z]+[1-9][0-9]*', cell_range):
                raise PrivateSheetError('Rango no permitido')
            a1 += '!' + cell_range
        url = ('https://sheets.googleapis.com/v4/spreadsheets/' +
               quote(spreadsheet_id, safe='') + '/values/' + quote(a1, safe=''))
        try:
            response = self.session.get(url, params={
                'majorDimension': 'ROWS', 'valueRenderOption': 'FORMATTED_VALUE'
            }, timeout=18, allow_redirects=False)
            if response.status_code != 200:
                raise PrivateSheetError('No se pudo leer la base privada')
            payload = response.json()
            rows = payload.get('values', [])
            if not isinstance(rows, list) or any(not isinstance(r, list) for r in rows):
                raise PrivateSheetError('Respuesta privada inválida')
            out = StringIO()
            writer = csv.writer(out)
            # Pad omitted trailing cells to preserve DataFrame column alignment.
            width = max((len(r) for r in rows), default=0)
            writer.writerows(r + [''] * (width-len(r)) for r in rows)
            return out.getvalue()
        except PrivateSheetError:
            raise
        except Exception:
            # Never expose response bodies, credential metadata or auth exceptions.
            raise PrivateSheetError('No se pudo leer la base privada') from None


def configured_reader(settings, allowed_sheets):
    """None preserves legacy public mode. Private errors NEVER fall back to it."""
    config = settings.get('PMS_SHEETS', {})
    mode = config.get('mode', 'public')
    if mode == 'public':
        return None
    if mode != 'private':
        raise PrivateSheetError('Modo de lectura desconocido')
    try:
        sid = config['spreadsheet_id']
        info = dict(settings['PMS_GOOGLE_SERVICE_ACCOUNT'])
        if (info.get('type') != 'service_account' or
                info.get('token_uri') != TOKEN_URI or
                info.get('universe_domain', 'googleapis.com') != 'googleapis.com'):
            raise ValueError('Untrusted credential configuration')
        # Do not accept custom URLs, delegation or external credential types.
        clean = {k: info[k] for k in ('type','client_email','private_key','token_uri')}
        if info.get('private_key_id'):
            clean['private_key_id'] = info['private_key_id']
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        credentials = service_account.Credentials.from_service_account_info(clean, scopes=[READ_SCOPE])
        return PrivateSheetReader(sid, allowed_sheets, AuthorizedSession(credentials))
    except Exception:
        raise PrivateSheetError('Configuración de lectura privada incompleta o inválida') from None
