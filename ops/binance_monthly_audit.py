"""Audited Binance Spot daily closes for monthly crypto prices in USD (USDT proxy).

Public endpoint; no API key, customer credentials, or balances required.
Never treats FUT/derivatives as spot cryptocurrency. Does not modify portfolio sheets.
"""
import argparse
import csv
import datetime as dt
import pathlib
import requests

BASE="https://data-api.binance.vision/api/v3/klines"
SUPPORTED={"BTC":"BTCUSDT","ETH":"ETHUSDT","ADA":"ADAUSDT"}
START=dt.date(2024,1,1)

def parse_monthly(candles, *, today=None):
    """Return last *completed* UTC daily close of each calendar month."""
    today=today or dt.datetime.now(dt.timezone.utc).date()
    last={}
    for bar in candles:
        try:
            date=dt.datetime.fromtimestamp(int(bar[0])/1000,dt.timezone.utc).date()
            close=float(bar[4])
            closed=dt.datetime.fromtimestamp(int(bar[6])/1000,dt.timezone.utc)
        except (IndexError,ValueError,TypeError,OverflowError):
            continue
        if not START<=date<today or closed>=dt.datetime.combine(today,dt.time.min,dt.timezone.utc):
            continue
        if close<=0 or not close<float("inf"):
            continue
        month=date.strftime("%Y-%m")
        if month not in last or last[month][0]<date:
            last[month]=(date,close)
    return [{"Mes":m,"Fecha cierre UTC":v[0].isoformat(),"Precio USDT":v[1]} for m,v in sorted(last.items())]

def fetch_symbol(symbol, *, session=None, end_date=None):
    if symbol not in SUPPORTED:
        raise ValueError("Ticker no soportado; FUT se valúa por separado")
    session=session or requests.Session()
    end_date=end_date or dt.datetime.now(dt.timezone.utc).date()
    current=int(dt.datetime(START.year,START.month,START.day,tzinfo=dt.timezone.utc).timestamp()*1000)
    stop=int(dt.datetime(end_date.year,end_date.month,end_date.day,tzinfo=dt.timezone.utc).timestamp()*1000)
    all_bars=[]
    while current<stop:
        response=session.get(BASE,params={"symbol":SUPPORTED[symbol],"interval":"1d",
            "startTime":current,"endTime":stop-1,"limit":1000},timeout=20)
        response.raise_for_status()
        batch=response.json()
        if not isinstance(batch,list):
            raise ValueError("Respuesta inesperada de Binance")
        if not batch:break
        all_bars.extend(batch)
        following=int(batch[-1][0])+86400000
        if following<=current:
            raise ValueError("Paginación no avanza")
        current=following
    return parse_monthly(all_bars,today=end_date)

def export(path):
    rows=[]
    for ticker in SUPPORTED:
        for bar in fetch_symbol(ticker):
            rows.append({"Mes":bar["Mes"],"Ticker":ticker,"Tipo":"Cripto",
                "Fecha cierre UTC":bar["Fecha cierre UTC"],"Precio USDT":bar["Precio USDT"],
                "Fuente":"Binance Spot 1d; USDT aproximado a USD","Estado":"PRECIO SIN CONCILIAR"})
    path=pathlib.Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=["Mes","Ticker","Tipo","Fecha cierre UTC","Precio USDT","Fuente","Estado"])
        writer.writeheader()
        writer.writerows(sorted(rows,key=lambda r:(r["Mes"],r["Ticker"])))
    return len(rows)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="data/binance_monthly_crypto_prices_audit.csv")
    args=parser.parse_args()
    print(f"Precios mensuales exportados: {export(args.out)}")
