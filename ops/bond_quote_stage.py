#!/usr/bin/env python3
"""Prepare auditable PMS bond rows. This script NEVER writes to Google Sheets."""
import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path
from bond_valuation_gate import assess, EXPECTED

HEADERS=["Fecha mercado","Ticker","Cierre ARS x 100 VN","Fuente","Estado","Fecha consulta","Nota","Valor USD ref."]

def finite_positive(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError("Value must be a numeric finite positive amount")
    if not math.isfinite(value) or value<=0:
        raise ValueError("Value must be finite and positive")
    return float(value)

def usd_per_vn(ars_per_100_vn, ars_per_usd):
    """Convert ARS/100 VN to USD/VN using an independently verified FX quote."""
    return finite_positive(ars_per_100_vn)/100.0/finite_positive(ars_per_usd)

def stage(payload, fx=None, today=None):
    gate=assess(payload,today=today)
    if not gate["safe_to_publish"]:
        return {"ready":False,"reasons":gate,"rows":[]}
    if not fx or fx.get("currency_pair")!="ARS/USD" or not fx.get("source") or not fx.get("market_date"):
        return {"ready":False,"reasons":["FX_SOURCE_OR_DATE_MISSING"],"rows":[]}
    try:
        fx_val=finite_positive(fx.get("ars_per_usd"))
        fx_day=dt.date.fromisoformat(fx["market_date"])
    except (ValueError,TypeError):
        return {"ready":False,"reasons":["INVALID_FX"],"rows":[]}
    if (today or dt.datetime.now(dt.timezone.utc).date())!=fx_day:
        return {"ready":False,"reasons":["FX_DATE_NOT_CURRENT"],"rows":[]}
    quotes={q["ticker"]:q for q in payload["quotes"]}
    rows=[]
    for t in sorted(EXPECTED):
        q=quotes[t]
        market_day=q["latest_row"]["market_date"]
        if market_day!=fx["market_date"]:
            return {"ready":False,"reasons":["FX_BOND_DATE_MISMATCH",t],"rows":[]}
        value=finite_positive(q["verified_close_ars_per_100_vn"])
        rows.append([market_day,t,round(value,6),q["source"],"VALIDADO_PARA_REVISION",
                     payload.get("generated_at_utc",""),
                     "USD por VN calculado con TC verificado y misma fecha: "+fx["source"],
                     round(usd_per_vn(value,fx_val),8)])
    return {"ready":True,"rows":rows,"reasons":[]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--quotes",default="iol_quotes_diagnostic.json")
    ap.add_argument("--fx",default="")
    ap.add_argument("--output",default="bond_staging_report.json")
    args=ap.parse_args()
    payload=json.loads(Path(args.quotes).read_text(encoding="utf-8"))
    fx=json.loads(Path(args.fx).read_text(encoding="utf-8")) if args.fx else None
    result=stage(payload,fx=fx)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"ready":result["ready"],"rows":len(result["rows"])}))
if __name__=="__main__":main()
