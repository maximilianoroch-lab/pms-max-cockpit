#!/usr/bin/env python3
"""Read-only IOL species-D snapshot. Market date and quotation unit are NOT inferred."""
import json, re, urllib.request, urllib.error
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from iol_probe import TICKERS

URL="https://iol.invertironline.com/mercado/cotizaciones/argentina/bonos"
class Table(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="tr":self.row=[]
        elif tag in ("th","td") and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ("th","td") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()));self.cell=None
        elif tag=="tr" and self.row is not None:
            self.rows.append(self.row);self.row=None

def parse_number(text):
    v=text.strip().replace(".","").replace(",",".")
    if not re.fullmatch(r"\d+(?:\.\d+)?",v):return None
    p=float(v)
    return p if p>0 and p<float("inf") else None

def parse(html):
    parser=Table();parser.feed(html)
    quotes={}
    for row in parser.rows:
        if not row:continue
        ticker=row[0].strip().upper()
        if ticker not in {t+"D" for t in TICKERS}:continue
        # First numeric column is a live Last/Último display, not a dated official close.
        last=parse_number(row[1]) if len(row)>1 else None
        if ticker in quotes:continue
        quotes[ticker]={"species":ticker,"display_last_usd_per_100_vn_candidate":last,
                         "raw_cells":row[:5],"verified_market_date":None,
                         "valuation_eligible":False,"reason":"UNDATED_LIVE_LAST_NOT_OFFICIAL_CLOSE"}
    return quotes

def main():
    quotes={}
    error=None
    try:
        req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=25) as r:
            html=r.read(3000000).decode("utf-8",errors="replace")
        quotes=parse(html)
    except (urllib.error.URLError,TimeoutError,OSError) as exc:error=str(exc)[:200]
    report={"captured_utc":datetime.now(timezone.utc).isoformat(),"source":URL,
            "purpose":"diagnostic_only","error":error,
            "instruments":[quotes.get(t+"D",{"species":t+"D","valuation_eligible":False,
                                            "reason":"NOT_FOUND"}) for t in TICKERS]}
    Path("iol_usd_bonds_diagnostic.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"found":len(quotes),"expected":len(TICKERS),"source_error":error}))
if __name__=="__main__":main()
