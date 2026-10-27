import datetime as dt
import unittest
from ops.binance_monthly_audit import parse_monthly,fetch_symbol

def bar(day,price):
    opened=int(dt.datetime.combine(day,dt.time.min,dt.timezone.utc).timestamp()*1000)
    return [opened,"1","1","1",str(price),"0",opened+86400000-1]

class BinanceHistoryTests(unittest.TestCase):
    def test_month_last_completed_close(self):
        rows=parse_monthly([bar(dt.date(2024,1,2),100),bar(dt.date(2024,1,31),110),
                            bar(dt.date(2024,2,1),120)],today=dt.date(2024,2,1))
        self.assertEqual(rows,[{"Mes":"2024-01","Fecha cierre UTC":"2024-01-31","Precio USDT":110.0}])
    def test_fut_is_not_crypto_spot(self):
        with self.assertRaises(ValueError):fetch_symbol("FUT")
if __name__=="__main__":unittest.main()
