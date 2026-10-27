"""Audit historical external price availability without exposing positions or accounts.

Outputs a per-instrument coverage report and a raw monthly price table.
Prices are *unverified* and must NOT be used for published historical valuation.
"""
import csv
import io
import pathlib
from collections import Counter
import requests
from ops.data912_monthly_audit import fetch_ticker
from ops.binance_monthly_audit import fetch_symbol, SUPPORTED

BASE="https://docs.google.com/spreadsheets/d/18qu9LXo55qQZq4oEAq42u_DKaI7e9lZL_PkfUZiu0T0/gviz/tq"

def sheet_rows(sheet,session):
    r=session.get(BASE,params={"tqx":"out:csv","sheet":sheet},timeout=40)
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))

def main():
    with requests.Session() as session:
        operations=sheet_rows("operaciones_normalizadas",session)
        price_targets=sorted({
            (row["Ticker"].strip().upper(),row["Tipo"].strip())
            for row in operations
            if row.get("Ticker") and row.get("Tipo") in ("Acción AR","Cedear","Bono AR")
        })
        out=[];coverage=[]
        for ticker,kind in price_targets:
            rows,status=fetch_ticker(session,ticker,kind,timeout=30)
            out.extend(rows)
            monthset={r["mes"] for r in rows if "2024-01"<=r["mes"]<="2026-10"}
            coverage.append({"ticker":ticker,"tipo":kind,"estado":status,
                "meses_2024_2026":len(monthset),"inicio":min(monthset) if monthset else "",
                "fin":max(monthset) if monthset else ""})
        for ticker in SUPPORTED:
            try:
                prices=fetch_symbol(ticker,session=session)
                count=len([x for x in prices if "2024-01"<=x["Mes"]<="2026-10"])
                status="OK" if prices else "SIN_PRECIOS"
            except (requests.RequestException,ValueError,TypeError) as exc:
                prices=[];count=0;status=type(exc).__name__
            coverage.append({"ticker":ticker,"tipo":"Cripto","estado":status,
                "meses_2024_2026":count,"inicio":prices[0]["Mes"] if prices else "",
                "fin":prices[-1]["Mes"] if prices else ""})
        root=pathlib.Path("market_audit");root.mkdir(exist_ok=True)
        with (root/"coverage.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(coverage[0]))
            w.writeheader();w.writerows(coverage)
        if out:
            with (root/"data912_monthly.csv").open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=list(out[0]))
                w.writeheader();w.writerows(out)
        print("Instrumentos:",len(coverage))
        print("Con menos de 30 meses:",sum(x["meses_2024_2026"]<30 for x in coverage))
        print("Estados:",dict(Counter(x["estado"] for x in coverage)))
        print("Resumen sin cifras de patrimonio, para auditar cobertura antes de valuar.")

if __name__=="__main__":
    main()
