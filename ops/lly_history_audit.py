"""Read-only LLY history anomaly report. No changes to Sheets or snapshots."""
import argparse
import csv
import datetime as dt
import json
from pathlib import Path


def price_number(value):
    s = str(value or "").strip().replace("$", "").replace(" ", "")
    if not s or s in {"-", "—"}:
        raise ValueError("Cotización vacía")
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        left, right = s.rsplit(",", 1)
        s = s.replace(",", "") if len(right) == 3 and left.isdigit() else s.replace(",", ".")
    elif s.count(".") == 1:
        left, right = s.split(".")
        if len(right) == 3 and left.isdigit() and right.isdigit():
            s = left + right
    value = float(s)
    if not 0 < value < float("inf"):
        raise ValueError("Cotización no positiva o inválida")
    return value


def market_day(value):
    value = str(value or "").strip().split(" ")[0]
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError("Fecha histórica no reconocida: " + value)


def audit_history(rows, evidence, relative_tolerance=0.03):
    """Report suspect LLY rows; comparisons are NOT approved corrective values."""
    candidates = {}
    for row in evidence:
        if str(row.get("ticker", "")).upper().strip() != "LLY":
            continue
        date = market_day(row.get("date"))
        if str(row.get("verification", "")).strip() != "REFERENCE_ONLY":
            raise ValueError("Este auditor solo acepta referencias identificadas como REFERENCE_ONLY")
        if date in candidates:
            raise ValueError("Referencia externa duplicada para " + date)
        candidates[date] = {
            "price_ars": price_number(row.get("price_ars")),
            "settlement": str(row.get("settlement", "")).strip(),
            "source": str(row.get("source", "")).strip(),
        }
    issues = []
    observed = 0
    for index, row in enumerate(rows, 2):
        if str(row.get("Ticker", "")).upper().strip() != "LLY":
            continue
        observed += 1
        try:
            date = market_day(row.get("Fecha"))
            raw_price = price_number(row.get("Precio"))
            currency = str(row.get("Moneda", "")).strip().upper()
        except ValueError as exc:
            issues.append({"row": index, "status": "INVALID_ORIGINAL_ROW", "detail": str(exc)})
            continue
        if currency != "ARS":
            issues.append({"row": index, "date": date, "status": "NOT_COMPARABLE_CURRENCY", "currency": currency})
            continue
        reference = candidates.get(date)
        if not reference:
            issues.append({"row": index, "date": date, "status": "NO_DATED_REFERENCE", "historic_ars": raw_price})
            continue
        difference_pct = (raw_price / reference["price_ars"] - 1) * 100
        if abs(difference_pct) > 100 * relative_tolerance:
            issues.append({
                "row": index, "date": date, "status": "SUSPECT_NOT_CERTIFIED",
                "historic_ars": raw_price, "reference_ars": reference["price_ars"],
                "difference_pct": round(difference_pct, 4),
                "reference_settlement": reference["settlement"],
                "reference_source": reference["source"],
            })
    return {"ticker": "LLY", "source": "export CSV de historial_precios",
            "read_only": True, "reference_certified": False,
            "rows_reviewed": observed, "issues": issues,
            "no_automatic_correction": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--references", type=Path, default=Path(__file__).with_name("lly_public_reference_sample.csv"))
    args = parser.parse_args()
    with args.history.open(encoding="utf-8-sig", newline="") as f:
        history = list(csv.DictReader(f))
    with args.references.open(encoding="utf-8-sig", newline="") as f:
        evidence = list(csv.DictReader(f))
    print(json.dumps(audit_history(history, evidence), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
