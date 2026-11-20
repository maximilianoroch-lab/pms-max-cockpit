import unittest
from unittest.mock import Mock, patch
from private_sheet_reader import PrivateSheetReader, PrivateSheetError, configured_reader


class PrivateReaderTests(unittest.TestCase):
    def reader(self, payload=None, status=200):
        session=Mock()
        session.get.return_value.status_code=status
        session.get.return_value.json.return_value=payload if payload is not None else {'values':[['Ticker','Valor USD'],['SYNTH','1.234,50']]}
        return PrivateSheetReader('synthetic-personal', {'feed', "O'Brien"}, session),session

    def test_formatted_values_use_fixed_api_and_readonly_get(self):
        reader,session=self.reader()
        self.assertIn('"1.234,50"',reader('synthetic-personal','feed','A1:B3'))
        args,kw=session.get.call_args
        self.assertEqual(args[0],"https://sheets.googleapis.com/v4/spreadsheets/synthetic-personal/values/%27feed%27%21A1%3AB3")
        self.assertEqual(kw['params']['valueRenderOption'],'FORMATTED_VALUE')
        self.assertFalse(kw['allow_redirects'])

    def test_no_cross_base_or_unknown_tab_request(self):
        reader,session=self.reader()
        for sid,sheet in [('synthetic-demo','feed'),('synthetic-personal','other')]:
            with self.assertRaises(PrivateSheetError): reader(sid,sheet)
        session.get.assert_not_called()

    def test_sheet_apostrophes_escaped(self):
        reader,session=self.reader()
        reader('synthetic-personal',"O'Brien")
        self.assertIn('%27O%27%27Brien%27',session.get.call_args.args[0])

    def test_rejects_range_injection_before_request(self):
        reader,session=self.reader()
        with self.assertRaises(PrivateSheetError): reader('synthetic-personal','feed',"A1:B3'!Other")
        session.get.assert_not_called()

    def test_ragged_rows_are_padded(self):
        reader,_=self.reader({'values':[['Ticker','Value'],['SYNTH']]})
        self.assertIn('SYNTH,\r\n',reader('synthetic-personal','feed'))

    def test_access_denied_redirect_and_network_failure_never_fallback(self):
        for status in (302,401,403,500):
            reader,session=self.reader(status=status)
            with self.assertRaises(PrivateSheetError): reader('synthetic-personal','feed')
            self.assertEqual(session.get.call_count,1)
        reader,session=self.reader()
        session.get.side_effect=Exception('SECRET_FIXTURE_MUST_NOT_LEAK')
        with self.assertRaises(PrivateSheetError) as caught: reader('synthetic-personal','feed')
        self.assertNotIn('SECRET_FIXTURE',str(caught.exception))

    def test_malformed_payload_rejected(self):
        reader,_=self.reader({'values':['bad row']})
        with self.assertRaises(PrivateSheetError): reader('synthetic-personal','feed')

    def test_private_missing_credentials_does_not_return_public(self):
        with self.assertRaises(PrivateSheetError): configured_reader({'PMS_SHEETS':{'mode':'private'}},{'feed'})
        self.assertIsNone(configured_reader({}, {'feed'}))
        with self.assertRaises(PrivateSheetError): configured_reader({'PMS_SHEETS':{'mode':'typo'}},{'feed'})

    def test_untrusted_token_endpoint_rejected(self):
        config={'PMS_SHEETS':{'mode':'private','spreadsheet_id':'synthetic-personal'},
                'PMS_GOOGLE_SERVICE_ACCOUNT':{'type':'service_account','token_uri':'https://invalid.example/token'}}
        with self.assertRaises(PrivateSheetError): configured_reader(config,{'feed'})

    def test_data_transport_does_not_retry_public_when_private_reader_fails(self):
        from data import read_sheet_csv
        reader=Mock(side_effect=PrivateSheetError('denied'))
        with patch('data.requests.get') as public:
            with self.assertRaises(PrivateSheetError): read_sheet_csv('synthetic-personal','feed',csv_reader=reader)
            public.assert_not_called()

    def test_all_feed_reads_use_private_transport(self):
        from data import load_all_data, FEEDS
        reader=Mock(return_value='Ticker,Valor USD\nSYNTH,1200\n')
        with patch('data.requests.get') as public:
            result=load_all_data('synthetic-personal',csv_reader=reader)
            self.assertEqual(set(result),set(FEEDS))
            self.assertEqual(reader.call_count,len(FEEDS))
            public.assert_not_called()

    def test_real_credential_constructor_requests_only_read_scope_without_network(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from private_sheet_reader import READ_SCOPE, TOKEN_URI
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        info={'type':'service_account','client_email':'synthetic@fixture.invalid',
              'private_key':key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
                                            serialization.NoEncryption()).decode(), 'token_uri':TOKEN_URI}
        reader=configured_reader({'PMS_SHEETS':{'mode':'private','spreadsheet_id':'synthetic-personal'},
                                  'PMS_GOOGLE_SERVICE_ACCOUNT':info},{'feed'})
        self.assertEqual(list(reader.session.credentials.scopes),[READ_SCOPE])
        self.assertEqual(reader.spreadsheet_id,'synthetic-personal')
        reader.session.close()


if __name__ == '__main__':
    unittest.main()
