"""Google OIDC authorization before personal data reads, including cache hits."""
import time

GOOGLE_METADATA = 'https://accounts.google.com/.well-known/openid-configuration'


def authorized_claims(claims, emails, subjects=(), now=None):
    now = time.time() if now is None else now
    email = str(claims.get('email', '')).strip().lower()
    subject = str(claims.get('sub', '')).strip()
    exp, issued = claims.get('exp'), claims.get('iat')
    numeric = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
    return bool(
        claims.get('iss') in {'accounts.google.com', 'https://accounts.google.com'}
        and claims.get('email_verified') is True and subject
        and email in {str(e).strip().lower() for e in emails}
        and (email.endswith('@gmail.com') or claims.get('hd'))
        and (not subjects or subject in subjects)
        and numeric(exp) and exp > now and numeric(issued)
        and now-8*3600 <= issued <= now+60
    )


def require_personal_user(st, settings):
    if settings.get('PMS_SHEETS', {}).get('mode', 'public') != 'private':
        return
    access = settings.get('PMS_ACCESS', {})
    emails, subjects = access.get('allowed_emails', []), access.get('allowed_subjects', [])
    auth = settings.get('auth', {})
    provider = auth.get('google', {})
    valid = (isinstance(emails, list) and bool(emails) and
             all(isinstance(e, str) and e.strip() for e in emails) and
             isinstance(subjects, list) and
             all(isinstance(s, str) and s.strip() for s in subjects) and
             provider.get('server_metadata_url') == GOOGLE_METADATA and
             provider.get('client_id') and provider.get('client_secret') and
             auth.get('cookie_secret') and auth.get('redirect_uri'))
    if not valid:
        st.error('El acceso privado requiere configurar el ingreso autorizado.')
        st.stop()
    if not st.user.is_logged_in:
        st.info('Ingresá con tu cuenta autorizada para ver la cartera personal.')
        if st.button('Ingresar con Google', key='personal_google_login'):
            st.login('google')
        st.stop()
    if not authorized_claims(dict(st.user), emails, subjects):
        st.error('Esta cuenta o sesión no tiene acceso a la cartera personal.')
        if st.button('Cerrar sesión', key='personal_denied_logout'):
            st.logout()
        st.stop()
    if st.sidebar.button('Cerrar sesión', key='personal_logout'):
        st.logout()
        st.stop()
