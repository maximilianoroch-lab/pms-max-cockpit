import unittest
from iol_probe import extract_rows,TICKERS
class TestIOL(unittest.TestCase):
    def test_dated_rows(self):
        html='<table><tr><td>10/16/2026</td><td>114,300</td><td>116,000</td><td>113,000</td><td>115,000</td></tr></table>'
        self.assertEqual(extract_rows(html)[0]['market_date'],'2026-10-16')
    def test_malformed(self):
        self.assertEqual(extract_rows('<tr><td>13/99/2026</td><td>x</td><td>x</td><td>x</td><td>x</td></tr>'),[])
    def test_all_tickers(self):self.assertEqual(len(TICKERS),6)
if __name__=='__main__':unittest.main()
