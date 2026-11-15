"""Read-only portfolio snapshot freshness gate.

Checks the *real* PMS Bersoch snapshot series, without modifying Sheets.
DEMO V5 has a separate independent history and must not use the copied DEMO Sheet.
"""
import csv
import datetime as dt
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

SHEET_ID = "18qu9LXo55qQZq4oEAq42u_DKaI7e9lZL_PkfUZiu0T0"
TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def parse_date(text):
    value = str(text or "").strip().split(" ")[0]
    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    raise ValueError("Invalid snapshot date")


def prior_business_date(today, holidays=frozenset()):
    """Last prior market session, excluding verified market holidays."""
    day = today - dt.timedelta(days=1)
    while day.weekday() >= 5 or day in holidays:
        day -= dt.timedelta(days=1)
    return day


def load_market_holidays(path):
    """Load explicitly maintained ISO market holidays; fail closed on malformed rows."""
    if not path:
        return frozenset()
    with open(path, encoding="utf-8-sig") as stream:
        rows = csv.DictReader(stream)
        if not rows.fieldnames or "date" not in rows.fieldnames:
            raise ValueError("Market holiday CSV must include a date column")
        days = set()
        for row in rows:
            value = str(row.get("date") or "").strip()
            if not value:
                continue
            try:
                parsed = dt.date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("Invalid market holiday date: " + value) from exc
            if parsed.isoformat() != value:
                raise ValueError("Market holiday dates must use YYYY-MM-DD")
            days.add(parsed)
        if not days:
            raise ValueError("Configured market holiday file contains no dates")
    return frozenset(days)


def assess_snapshots(rows, today, holidays=frozenset()):
    dates = []
    for row in rows:
        raw = row.get("Fecha", "")
        try:
            dates.append(parse_date(raw))
        except ValueError:
            continue
    if not dates:
        return {"status": "MISSING", "latest": None, "expected": prior_business_date(today, holidays).isoformat(),
                "missing_weekdays": None}
    latest = max(dates)
    expected = prior_business_date(today, holidays)
    missing = sum(1 for offset in range(1, (today-latest).days)
                  if (latest+dt.timedelta(days=offset)).weekday() < 5 and (latest+dt.timedelta(days=offset)) not in holidays) if today > latest else 0
    return {"status": "LATE" if latest < expected else "OK", "latest": latest.isoformat(),
            "expected": expected.isoformat(), "missing_weekdays": missing}


def read_sheet(name):
    url = "https://docs.google.com/spreadsheets/d/" + SHEET_ID + "/gviz/tq?" + urllib.parse.urlencode(
        {"tqx": "out:csv", "sheet": name}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "PMS-integrity-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=35) as response:
        return list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig"))))


def assess_integrity(rows):
    lookup = {str(row.get("Control", "")).strip(): row for row in rows}
    expected = {"Posiciones sin valor": "0", "Caja conciliación USD": "0", "Snapshot apto": "APTO"}
    failing = []
    for label, target in expected.items():
        entry = lookup.get(label)
        if entry is None:
            failing.append("Missing control: " + label)
            continue
        if label == "Snapshot apto":
            observed = str(entry.get("Estado", "")).strip().upper()
        else:
            observed = str(entry.get("Valor", "")).strip()
        if observed != target:
            failing.append(label + ": " + (observed or "(blank)"))
    return failing


def main():
    today = dt.datetime.now(TZ).date()
    calendar_path = os.environ.get("PMS_MARKET_HOLIDAYS_CSV", "").strip()
    output = {"audited_at_local": dt.datetime.now(TZ).isoformat(), "portfolio": "Bersoch",
              "read_only": True, "market_holidays_not_modeled": not bool(calendar_path)}
    try:
        holidays = load_market_holidays(calendar_path)
        output["market_holiday_calendar"] = "verified_external_csv" if calendar_path else "none"
        snapshot = assess_snapshots(read_sheet("snapshot_series_v2"), today, holidays)
        integrity = assess_integrity(read_sheet("control_integridad_v2"))
        output["snapshot"] = snapshot
        output["integrity_problems"] = integrity
    except (OSError, ValueError, KeyError, csv.Error) as exc:
        output["error"] = type(exc).__name__ + ": " + str(exc)[:160]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2))
    # A missing weekday can coincide with an Argentinian market holiday.
    # Emit failure to prompt review, never synthesize prices or a snapshot.
    if snapshot["status"] != "OK" or integrity:
        print("::error::Bersoch cierres pendientes o control de integridad inválido. Revisar fechas, feriados y fuentes.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
