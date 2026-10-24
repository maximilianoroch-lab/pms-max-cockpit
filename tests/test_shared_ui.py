import unittest
from pms_shared_ui import style_bar,fmt_usd,fmt_pct_fraction,fmt_number
class StubFigure:
 def __init__(self):self.trace=None;self.layout=None;self.y=None;self.x=None
 def update_traces(self,**kw):self.trace=kw
 def update_layout(self,**kw):self.layout=kw
 def update_yaxes(self,**kw):self.y=kw
 def update_xaxes(self,**kw):self.x=kw
class SharedUI(unittest.TestCase):
 def test_bar_style(self):
  f=StubFigure()
  self.assertIs(style_bar(f),f)
  self.assertEqual(f.layout["barcornerradius"],6)
  self.assertEqual(f.trace["marker_line_width"],1.2)
  self.assertEqual(f.y["categoryorder"],"total ascending")
  self.assertEqual(f.layout["bargap"],0.48)
  self.assertEqual(f.x["gridcolor"],"rgba(160,191,220,0.09)")
 def test_shared_table_and_card(self):
  from pms_shared_ui import render_financial_table,render_kpi_card
  class FakeStreamlit:
   def dataframe(self,frame,**kwargs):
    self.table_kwargs=kwargs
    return "table"
   def markdown(self,value,**kwargs):
    self.card_markup=value
    return "card"
  fake=FakeStreamlit()
  self.assertEqual(render_financial_table(fake,[1,2]),"table")
  self.assertTrue(fake.table_kwargs["hide_index"])
  self.assertEqual(render_kpi_card(fake,"Test","US$ 10","<example>"),"card")
  self.assertIn("&lt;example&gt;",fake.card_markup)
 def test_format(self):
  self.assertEqual(fmt_usd(1234567),"US$ 1.234.567")
  self.assertEqual(fmt_pct_fraction(.1234),"12,3%")
  self.assertEqual(fmt_number(1234567.25,2),"1.234.567,25")
  self.assertEqual(fmt_usd(None),"—")
  self.assertEqual(fmt_pct_fraction(float("nan")),"—")
if __name__=="__main__":unittest.main()
