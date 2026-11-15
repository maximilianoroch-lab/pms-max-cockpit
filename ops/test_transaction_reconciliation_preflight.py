import unittest
from ops.transaction_reconciliation_preflight import reconcile

CUSTODY = [{"Broker":"ALPHA","Ticker":"ABC","Cantidad":"100"},
           {"Broker":"BETA","Ticker":"DEF","Cantidad":"200"}]


def trade(**overrides):
    row = {"Referencia":"MOV1","Fecha":"2026-11-13","Broker":"ALPHA",
           "Ticker":"ABC","Movimiento":"VENTA","Cantidad":"10",
           "Importe":"150000","Moneda":"ARS"}
    row.update(overrides)
    return row


class TransactionPreflightTests(unittest.TestCase):
    def test_missing_date_blocks_posting(self):
        result=reconcile([trade(Fecha="")],CUSTODY)
        self.assertEqual(result["faltan_fechas"],["MOV1"])
        self.assertEqual(result["movimientos_aplicados"],0)
    def test_dated_transaction_is_still_not_posted(self):
        result=reconcile([trade()],CUSTODY)
        self.assertEqual(result["pendientes_de_registro_o_conciliacion"],["MOV1"])
        self.assertEqual(result["registros_con_fecha_valida"][0]["custodia_actual"],"100")
        self.assertEqual(result["movimientos_aplicados"],0)
    def test_cash_transfer_no_instrument_quantity(self):
        result=reconcile([trade(Movimiento="DEPOSITO",Ticker="",Cantidad="0")],CUSTODY)
        self.assertEqual(len(result["pendientes_de_registro_o_conciliacion"]),1)
    def test_duplicate_reference_fails(self):
        with self.assertRaisesRegex(ValueError,"duplicada"):
            reconcile([trade(),trade()],CUSTODY)
    def test_bad_amount_fails(self):
        with self.assertRaises(ValueError):
            reconcile([trade(Importe="-5")],CUSTODY)
    def test_broker_ticker_custody_duplicate_fails(self):
        with self.assertRaisesRegex(ValueError,"duplicada"):
            reconcile([],CUSTODY+CUSTODY[:1])

if __name__=="__main__":
    unittest.main()
