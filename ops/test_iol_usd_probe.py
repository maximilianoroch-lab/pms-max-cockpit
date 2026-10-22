import unittest
from iol_usd_probe import parse,parse_number
class TestUsdProbe(unittest.TestCase):
    def test_species_not_pesos(self):
        sample='<table><tr><td>AN29</td><td>135.000,00</td></tr><tr><td>AN29D</td><td>88,25</td></tr></table>'
        quotes=parse(sample)
        self.assertEqual(quotes["AN29D"]["display_last_usd_per_100_vn_candidate"],88.25)
        self.assertFalse(quotes["AN29D"]["valuation_eligible"])
    def test_number(self):
        self.assertEqual(parse_number("1.234,50"),1234.5)
        self.assertIsNone(parse_number("-"))
if __name__=="__main__":unittest.main()
