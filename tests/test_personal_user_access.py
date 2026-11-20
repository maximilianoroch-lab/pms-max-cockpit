import unittest
from unittest.mock import Mock
from personal_user_access import authorized_claims, require_personal_user, GOOGLE_METADATA
class Stop(Exception): pass
class AccessTests(unittest.TestCase):
    def claims(self, **kw):
        return dict({'iss':'https://accounts.google.com','sub':'synthetic-sub','email':'owner@gmail.com',
                     'email_verified':True,'iat':1000,'exp':5000},**kw)
    def test_authorized_account(self):
        self.assertTrue(authorized_claims(self.claims(),['owner@gmail.com'],now=2000))
    def test_rejections(self):
        for kw in ({'iss':'https://evil.invalid'}, {'sub':''}, {'email':'other@gmail.com'},
                   {'email_verified':'true'}, {'email_verified':False}, {'exp':2000},
                   {'exp':'5000'}, {'iat':3000}, {'iat':-30000}, {'email':'owner@external.invalid'}):
            self.assertFalse(authorized_claims(self.claims(**kw),['owner@gmail.com','owner@external.invalid'],now=2000),kw)
    def test_subject_binding(self):
        self.assertFalse(authorized_claims(self.claims(),['owner@gmail.com'],['different'],now=2000))
    def config(self):
        return {'PMS_SHEETS':{'mode':'private'},'PMS_ACCESS':{'allowed_emails':['owner@gmail.com']},
                'auth':{'cookie_secret':'synthetic','redirect_uri':'https://fixture.invalid/oauth2callback',
                        'google':{'server_metadata_url':GOOGLE_METADATA,'client_id':'synthetic','client_secret':'synthetic'}}}
    def st(self):
        st=Mock();st.stop.side_effect=Stop;st.user=Mock(is_logged_in=False)
        st.button.return_value=False;st.sidebar.button.return_value=False
        return st
    def test_missing_config_blocks(self):
        st=self.st()
        with self.assertRaises(Stop): require_personal_user(st,{'PMS_SHEETS':{'mode':'private'}})
        st.error.assert_called_once();st.login.assert_not_called()
    def test_logged_out_blocks(self):
        st=self.st()
        with self.assertRaises(Stop): require_personal_user(st,self.config())
        st.login.assert_not_called()
    def test_login_on_click(self):
        st=self.st();st.button.return_value=True
        with self.assertRaises(Stop): require_personal_user(st,self.config())
        st.login.assert_called_once_with('google')
    def test_public_unchanged(self):
        st=self.st();require_personal_user(st,{})
        st.stop.assert_not_called()
    def test_guard_before_cache(self):
        from pathlib import Path
        source=Path('app.py').read_text()
        self.assertLess(source.index('require_personal_user(st,'),source.index('data=get_data()'))
if __name__=='__main__': unittest.main()
