"""Read-only preflight for missing PMS snapshot dates.

Input files are locally provided exports, never live positions downloaded here.
Outputs coverage gaps ONLY. A passing coverage check is NOT a certified closing
valuation: unit conventions, corporate actions, cash and settlement still need audit.
"""
import argparse
import csv
import datetime as dt
import json


def norm_date(value):
    try:
        return dt.date.fromisoformat(str(value or "").strip()).isoformat()
    except ValueError as exc:
        raise ValueError("Fecha no válida; se requiere AAAA-MM-DD") from exc


def audit_snapshot_coverage(positions, quotes, dates):
    """Check complete dated ticker quantities and quotes before historical backfill."""
    requested = [norm_date(x) for x in dates]
    if len(set(requested)) != len(requested):
        raise ValueError("Fechas solicitadas duplicadas")
    holdings = {}
    for row in positions:
        date = norm_date(row.get("Fecha"))
        ticker = str(row.get("Ticker", "")).strip().upper()
        if not ticker:
            raise ValueError("Posición sin ticker")
        try:
            quantity = float(str(row.get("Cantidad", "")).replace(",", "."))
        except ValueError as exc:
            raise ValueError("Cantidad inválida en " + ticker) from exc
        if not 0 <= quantity < float("inf"):
            raise ValueError("Cantidad fuera de rango en " + ticker)
        key = date, ticker
        if key in holdings:
            raise ValueError("Posición duplicada por ticker y fecha: " + str(key))
        holdings[key] = quantity
    observations = {}
    for row in quotes:
        date = norm_date(row.get("Fecha"))
        ticker = str(row.get("Ticker", "")).strip().upper()
        key = date, ticker
        if key in observations:
            raise ValueError("Cotización duplicada por ticker y fecha: " + str(key))
        price = str(row.get("Precio", "")).strip()
        source = str(row.get("Fuente", "")).strip()
        currency = str(row.get("Moneda", "")).strip().upper()
        at = str(row.get("Corte", "")).strip()
        try:
            number = float(price.replace(",", "."))
        except ValueError:
            number = float("nan")
        observations[key] = bool(number > 0 and number < float("inf")
                                  and source and currency in ("USD", "ARS") and at)
    report = []
    for date in requested:
        tickers = sorted(t for (day, t), qty in holdings.items() if day == date and qty > 0)
        if not tickers:
            report.append({"fecha": date, "estado": "FALTAN_TENENCIAS_FECHADAS",
                           "activos": 0, "cotizaciones_validas": 0, "faltantes": []})
            continue
        missing = [t for t in tickers if not observations.get((date, t), False)]
        report.append({"fecha": date, "estado": "PENDIENTE" if missing else "COBERTURA_PRELIMINAR_COMPLETA",
                       "activos": len(tickers), "cotizaciones_validas": len(tickers)-len(missing),
                       "faltantes": missing})
    return {"solo_lectura": True, "cierre_certificado": False,
            "requiere_conciliacion_caja_fx_corporativos": True, "fechas": report}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--positions", required=True)
    parser.add_argument("--quotes", required=True)
    parser.add_argument("--dates", nargs="+", default=["2026-11-12", "2026-11-13"])
    args = parser.parse_args()
    with open(args.positions, encoding="utf-8-sig", newline="") as fh:
        positions = list(csv.DictReader(fh))
    with open(args.quotes, encoding="utf-8-sig", newline="") as fh:
        quotes = list(csv.DictReader(fh))
    print(json.dumps(audit_snapshot_coverage(positions, quotes, args.dates),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
