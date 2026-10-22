#!/usr/bin/env python3
"""Validate the diagnostic envelope, never promote unchecked quotes into PMS."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

EXPECTED={"AN29","AO28","AO29","GD35","GD38","GD41"}
REQUIRED_UNITS="ARS_PER_100_VN"
MAX_AGE_DAYS=5

def assess(payload, today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    quotes=payload.get("quotes",[])
    seen=set()
    rows=[]
    for q in quotes:
        symbol=str(q.get("ticker","")).upper()
        reasons=[]
        if symbol not in EXPECTED: reasons.append("UNKNOWN_TICKER")
        if symbol in seen: reasons.append("DUPLICATE_TICKER")
        seen.add(symbol)
        if q.get("currency")!="ARS":reasons.append("CURRENCY_UNVERIFIED")
        if q.get("unit")!=REQUIRED_UNITS:reasons.append("UNIT_UNVERIFIED")
        last=q.get("latest_row") or {}
        try:
            day=dt.date.fromisoformat(last["market_date"])
            if day>today or (today-day).days>MAX_AGE_DAYS: reasons.append("STALE_OR_FUTURE_DATE")
        except (KeyError,TypeError,ValueError):reasons.append("MISSING_MARKET_DATE")
        if q.get("error"): reasons.append("SOURCE_ERROR")
        if not q.get("source","").startswith("https://iol.invertironline.com/"):
            reasons.append("UNTRUSTED_SOURCE")
        # The diagnostic has no validated numeric close column yet.
        close=q.get("verified_close_ars_per_100_vn")
        if isinstance(close,bool) or not isinstance(close,(int,float)) or not math.isfinite(close) or close<=0:
            reasons.append("CLOSE_NOT_VERIFIED")
        if q.get("verified_market_date")!=last.get("market_date"):
            reasons.append("CLOSE_DATE_NOT_ATTESTED")
        if q.get("unit_evidence") not in ("BROKER_DOCUMENTED", "EXCHANGE_DOCUMENTED"):
            reasons.append("UNIT_EVIDENCE_MISSING")
        if q.get("currency_evidence") not in ("BROKER_DOCUMENTED", "EXCHANGE_DOCUMENTED"):
            reasons.append("CURRENCY_EVIDENCE_MISSING")
        if q.get("valuation_eligible") is not True:
            reasons.append("SOURCE_NOT_APPROVED")
        rows.append({"ticker":symbol,"eligible":not reasons,"reasons":reasons,
                     "market_date":last.get("market_date"),"source":q.get("source")})
    missing=sorted(EXPECTED-seen)
    return {"safe_to_publish":not missing and len(rows)==len(EXPECTED) and all(r["eligible"] for r in rows),
            "missing_tickers":missing,"checks":rows,
            "policy":"Do not write to the portfolio or bonos_auto_v2 before explicit unit and currency verification."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="iol_quotes_diagnostic.json")
    p.add_argument("--output",default="bond_valuation_gate.json")
    args=p.parse_args()
    payload=json.loads(Path(args.input).read_text(encoding="utf-8"))
    result=assess(payload)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"safe_to_publish":result["safe_to_publish"],
                      "missing":result["missing_tickers"],
                      "blocked":sum(not row["eligible"] for row in result["checks"])}))
if __name__=="__main__": main()
