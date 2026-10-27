"""Conservative Data912 historical OHLC collection for Bersoch.

This source is educational, not an official validated closing-price source.
Writes *only* an audit CSV; never changes portfolio valuations or Google Sheets.
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import time
from urllib.parse import quote
import requests

KIND={"Acción AR":"stocks","Cedear":"cedears","Bono AR":"bonds"}
START=dt.date(2024,1,1)

def month_closes(records,ticker,kind):
    latest={}
    for p in records:
        try:
            date=dt.date.fromisoformat(str(p["date"])[:10])
            close=float(p["c"])
        except (KeyError,ValueError,TypeError):
            continue
        if date<START or close<=0 or not (close<float("inf")):
            continue
        month=date.strftime("%Y-%m")
        if month not in latest or date>latest[month][0]:
            latest[month]=(date,close)
    return [{"mes":m,"fecha_precio":v[0].isoformat(),"ticker":ticker,
        "tipo":kind,"cierre_ars":v[1],"fuente":"Data912 /historical (educativo; sin validar)"}
        for m,v in sorted(latest.items())]

def fetch_ticker(session,ticker,kind,timeout=18):
    endpoint=KIND.get(kind)
    if not endpoint:
        return [],"NO_CUBIERTO"
    url=f"https://data912.com/historical/{endpoint}/{quote(ticker,safe='')}"
    try:
        result=session.get(url,timeout=timeout)
        result.raise_for_status()
        records=result.json()
        if not isinstance(records,list):
            return [],"FORMATO_INESPERADO"
        rows=month_closes(records,ticker,kind)
        return rows,"OK" if rows else "SIN_PRECIOS"
    except (requests.RequestException,ValueError,TypeError) as exc:
        return [],type(exc).__name__

def collect(inventory,output,report,delay=.55):
    output=pathlib.Path(output)
    inventory=pathlib.Path(inventory)
    symbols={}
    with inventory.open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            ticker=(row.get("Ticker") or "").strip().upper()
            kind=(row.get("Tipo") or "").strip()
            if ticker and kind in KIND:
                symbols[(ticker,kind)]=True
    all_rows=[];audit=[]
    with requests.Session() as session:
        for ticker,kind in sorted(symbols):
            rows,status=fetch_ticker(session,ticker,kind)
            all_rows.extend(rows)
            audit.append({"ticker":ticker,"tipo":kind,"estado":status,
                 "meses":len(rows),"primer_mes":rows[0]["mes"] if rows else "",
                 "ultimo_mes":rows[-1]["mes"] if rows else ""})
            time.sleep(delay)
    output.parent.mkdir(parents=True,exist_ok=True)
    report=pathlib.Path(report);report.parent.mkdir(parents=True,exist_ok=True)
    def write(path,fields,rows):
        with path.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    write(output,["mes","fecha_precio","ticker","tipo","cierre_ars","fuente"],all_rows)
    write(report,["ticker","tipo","estado","meses","primer_mes","ultimo_mes"],audit)
    return len(symbols),len(all_rows)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--inventory",required=True,help="CSV con encabezados Ticker,Tipo (sin números de cuenta)")
    parser.add_argument("--out",default="data/data912_monthly_prices_audit.csv")
    parser.add_argument("--report",default="data/data912_coverage_audit.csv")
    args=parser.parse_args()
    n,m=collect(args.inventory,args.out,args.report)
    print(json.dumps({"instrumentos_solicitados":n,"filas_mensuales_sin_validar":m}))
