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
  self.assertEqual(f.layout["barcornerradius"],5)
  self.assertEqual(f.trace["marker_line_width"],1.6)
  self.assertEqual(f.y["categoryorder"],"total ascending")
 def test_format(self):
  self.assertEqual(fmt_usd(1234567),"US$ 1.234.567")
  self.assertEqual(fmt_pct_fraction(.1234),"12,3%")
  self.assertEqual(fmt_number(1234567.25,2),"1.234.567,25")
  self.assertEqual(fmt_usd(None),"—")
  self.assertEqual(fmt_pct_fraction(float("nan")),"—")
if __name__=="__main__":unittest.main()
