"""Reconcile historical purchase/sale share movements to currently held quantities.
No position values, accounts, or monetary data are printed or uploaded.
"""
import csv,io,requests
from collections import defaultdict
SHEET="18qu9LXo55qQZq4oEAq42u_DKaI7e9lZL_PkfUZiu0T0"
BASE=f"https://docs.google.com/spreadsheets/d/{SHEET}/gviz/tq"
def rows(s,name):
 r=s.get(BASE,params={"tqx":"out:csv","sheet":name},timeout=45)
 r.raise_for_status()
 return list(csv.DictReader(io.StringIO(r.text)))
def number(value):
 try:
  v=str(value).strip().replace(" ","").replace("$","")
  if "," in v and "." in v:
   v=v.replace(".","").replace(",",".") if v.rfind(",")>v.rfind(".") else v.replace(",","")
  else:v=v.replace(",",".")
  return float(v)
 except (ValueError,TypeError):return 0.
def main():
 with requests.Session() as session:
  operations=rows(session,"operaciones_normalizadas")
  actual=rows(session,"app_feed_v2")
 delta=defaultdict(float)
 for op in operations:
  if op.get("Evento") in ("Compra","Venta","Dividendo en acciones","Split"):
   t=op.get("Ticker","").strip().upper()
   if t:delta[t]+=number(op.get("Cantidad"))
 observed={r.get("Ticker","").upper():number(r.get("Cantidad")) for r in actual if r.get("Ticker")}
 mismatches=[]
 for t in set(delta)|set(observed):
  expected=observed.get(t,0)
  err=delta.get(t,0)-expected
  if abs(err)>max(.0001,abs(expected)*.001):
   mismatches.append(t)
 print("Instrumentos con movimientos de cantidad:",len(delta))
 print("Instrumentos en cartera actual:",len(observed))
 print("Instrumentos sin conciliación de cantidad:",len(mismatches))
 print("TICKERS_NO_CONCILIADOS:",", ".join(sorted(mismatches)))
 print("AVISO: pueden existir amortizaciones y eventos no modelados; no valuar hasta conciliar.")
if __name__=="__main__":main()
