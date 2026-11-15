"""Read-only audit: flag observations on dates without BYMA trading.

A whole-portfolio snapshot on a BYMA holiday may still reflect US/crypto
market activity. It must not be deleted or automatically called fabricated.
"""
import csv
import datetime as dt
import json
from pathlib import Path


def _date(value):
    s=str(value or "").strip().split()[0]
    for fmt in ("%Y-%m-%d","%d/%m/%Y"):
        try:
            return dt.datetime.strptime(s,fmt).date()
        except ValueError:
            pass
    return None


def audit_trading_dates(snapshot_rows, byma_closed_dates):
    closed={dt.date.fromisoformat(str(d)) for d in byma_closed_dates}
    flagged=[]
    for index,row in enumerate(snapshot_rows,2):
        day=_date(row.get("Fecha"))
        if day is None:
            flagged.append({"row":index,"fecha":str(row.get("Fecha")),"status":"FECHA_INVALIDA"})
            continue
        if day in closed:
            flagged.append({
                "row":index,"fecha":day.isoformat(),
                "status":"BYMA_CERRADO_PATRIMONIO_MULTIMERCADO_REVISAR",
                "fuente":str(row.get("Fuente","")),
                "accion":"Conservar original; verificar US/cripto y marcar ausencia de rueda BYMA"
            })
    return {"solo_lectura":True,"automatic_corrections":False,
            "registros_revisados":len(snapshot_rows),"alertas":flagged}


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--byma-calendar",type=Path,required=True)
    args=p.parse_args()
    with args.snapshots.open(encoding="utf-8-sig",newline="") as f:
        snapshots=list(csv.DictReader(f))
    with args.byma_calendar.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    closed=[x["date"] for x in rows]
    print(json.dumps(audit_trading_dates(snapshots,closed),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
