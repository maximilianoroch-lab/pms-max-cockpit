"""Tests of the IOL historical HTML parsing contract; no market write."""
from html.parser import HTMLParser
from datetime import datetime

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_td=False; self.in_tr=False; self.cell=""; self.row=[]; self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=="tr":self.in_tr=True;self.row=[]
        if tag in ("td","th") and self.in_tr:self.in_td=True;self.cell=""
    def handle_data(self,data):
        if self.in_td:self.cell+=data
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.in_td:self.row.append(self.cell.strip());self.in_td=False
        if tag=="tr" and self.in_tr:self.rows.append(self.row);self.in_tr=False

def parse_html(html):
    p=Rows();p.feed(html);out=[]
    for row in p.rows:
        if len(row)<8:continue
        try:
            dt=datetime.strptime(row[0],"%m/%d/%Y").date()
            nums=[float(x.replace(",","")) for x in row[1:8]]
            op,hi,lo,close,adj,amt,vol=nums
            if min(op,hi,lo,close,adj,amt,vol)<=0 or lo>hi or close<lo*.95 or close>hi*1.05:continue
            out.append((dt,close))
        except(ValueError,TypeError):continue
    return sorted(out,reverse=True)

def test_known_gd35():
    h="<table><tr><th>Fecha</th></tr><tr>"+ "".join("<td>"+v+"</td>" for v in
    ["10/16/2026","115,700.00","116,490.00","114,250.00","114,300.00","114,300.00","10,706,321,824.10","9,289,519.00"] )+"</tr></table>"
    assert str(parse_html(h)[0][0])=="2026-10-16"
    assert parse_html(h)[0][1]==114300
def test_reject_malformed():
    assert parse_html("<table><tr><td>10/16/2026</td><td>0</td></tr></table>")==[]
if __name__=="__main__":
    test_known_gd35();test_reject_malformed();print("2 pruebas OK")
