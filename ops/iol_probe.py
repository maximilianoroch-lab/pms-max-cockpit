#!/usr/bin/env python3
"""Read-only public IOL probe. NEVER a portfolio valuation source."""
import argparse, json, re, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
TICKERS=('AN29','AO28','AO29','GD35','GD38','GD41')
BASE='https://iol.invertironline.com/Titulo/DatosHistoricos?mercado=BCBA&simbolo='
DATE=re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')
class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr': self.row=[]
        elif tag in ('td','th') and self.row is not None: self.cell=[]
    def handle_data(self,data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell=None
        elif tag=='tr' and self.row is not None:
            self.rows.append(self.row); self.row=None
def extract_rows(html):
    p=TableParser(); p.feed(html); hits=[]
    for row in p.rows:
        if len(row)<5 or not DATE.fullmatch(row[0]):continue
        try: date=datetime.strptime(row[0],'%m/%d/%Y').date()
        except ValueError:continue
        hits.append({'market_date':date.isoformat(),'cells':row})
    return sorted(hits,key=lambda x:x['market_date'],reverse=True)
def probe(ticker,timeout=18):
    url=BASE+urllib.parse.quote(ticker)
    result={'ticker':ticker,'source':url,'valuation_eligible':False,'unit':'UNVERIFIED','currency':'UNVERIFIED'}
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PMS-ReadOnly/1.0)'})
        with urllib.request.urlopen(request,timeout=timeout) as response:
            html=response.read(2000000).decode('utf-8',errors='replace')
            result['http_status']=response.status
        rows=extract_rows(html);result['matching_rows']=len(rows)
        if rows:result['latest_row']=rows[0]
        else:result['error']='No dated table rows; page may require JavaScript or block clients'
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError) as exc:
        result['error']=str(exc)[:300]
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='iol_quotes_diagnostic.json')
    args=p.parse_args()
    data={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'purpose':'diagnostic_only',
          'never_use_as_valuation':True,'quotes':[probe(t) for t in TICKERS]}
    Path(args.output).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'tickers':len(data['quotes']),'date_rows_found':sum(bool(q.get('matching_rows')) for q in data['quotes']),
                      'errors':[q['ticker'] for q in data['quotes'] if q.get('error')]}))
if __name__=='__main__':main()
