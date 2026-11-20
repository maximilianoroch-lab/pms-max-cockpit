"""Read-only transactions vs account inventory reconciliation (no private fixture data).

Never writes operations, balances, Sheets or broker accounts. The two inputs
are local, explicitly supplied CSV exports; duplicate dates/operations must be
resolved by an operator. Unknown execution dates block posting.
"""
import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation


def decimal(value):
    val = str(value if value is not None else "").strip().replace(" ", "")
    if not val:
        raise ValueError("Monto o cantidad sin informar")
    if "," in val and "." in val:
        val = val.replace(".", "").replace(",", ".") if val.rfind(",") > val.rfind(".") else val.replace(",", "")
    elif "," in val:
        val = val.replace(",", ".")
    try:
        result = Decimal(val)
    except InvalidOperation as exc:
        raise ValueError("Monto o cantidad no numérico") from exc
    if not result.is_finite():
        raise ValueError("Monto no finito")
    return result


def reconcile(trades, custody_rows):
    """Explicit posted trades only; pending dates produce a blocker."""
    seen = set()
    positions = {}
    for row in custody_rows:
        broker, ticker = str(row.get("Broker", "")).strip().upper(), str(row.get("Ticker", "")).strip().upper()
        if not broker or not ticker:
            raise ValueError("Fila de custodia sin broker/ticker")
        key = broker, ticker
        if key in positions:
            raise ValueError("Custodia duplicada por broker/ticker")
        qty = decimal(row.get("Cantidad"))
        if qty < 0:
            raise ValueError("Cantidad negativa en custodia")
        positions[key] = qty

    missing_dates, pending_posting, validated = [], [], []
    for row in trades:
        token = str(row.get("Referencia", "")).strip()
        broker = str(row.get("Broker", "")).strip().upper()
        ticker = str(row.get("Ticker", "")).strip().upper()
        action = str(row.get("Movimiento", "")).strip().upper()
        date = str(row.get("Fecha", "")).strip()
        if not token or token in seen:
            raise ValueError("Referencia vacía o duplicada")
        seen.add(token)
        if action not in {"COMPRA", "VENTA", "DEPOSITO", "RETIRO"} or not broker:
            raise ValueError("Movimiento/broker inválido")
        qty = decimal(row.get("Cantidad"))
        amount = decimal(row.get("Importe"))
        if amount <= 0 or qty < 0:
            raise ValueError("Importe/cantidad fuera de rango")
        if action in {"COMPRA", "VENTA"} and (qty <= 0 or not ticker):
            raise ValueError("Operación de títulos sin ticker/cantidad")
        if action in {"DEPOSITO", "RETIRO"} and qty != 0:
            raise ValueError("Flujos de fondos deben tener cantidad cero")
        # Blank or malformed dates are NOT guessed from the portfolio's as-of.
        try:
            import datetime as dt
            parsed = dt.date.fromisoformat(date).isoformat()
        except ValueError:
            missing_dates.append(token)
            continue
        if not str(row.get("Moneda", "")).strip().upper() in {"ARS", "USD"}:
            raise ValueError("Moneda no válida")
        pending_posting.append(token)
        validated.append({"referencia": token, "fecha": parsed, "broker": broker,
                          "ticker": ticker, "movimiento": action, "cantidad": str(qty),
                          "custodia_actual": str(positions.get((broker, ticker), "NO_EXISTE"))})
    return {
        "solo_lectura": True,
        "movimientos_inspeccionados": len(trades),
        "faltan_fechas": missing_dates,
        "pendientes_de_registro_o_conciliacion": pending_posting,
        "registros_con_fecha_valida": validated,
        "movimientos_aplicados": 0,
        "cierre_historico_certificado": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--movements", required=True)
    parser.add_argument("--custody", required=True)
    args = parser.parse_args()
    with open(args.movements, newline="", encoding="utf-8-sig") as f:
        movements = list(csv.DictReader(f))
    with open(args.custody, newline="", encoding="utf-8-sig") as f:
        custody = list(csv.DictReader(f))
    print(json.dumps(reconcile(movements, custody), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
