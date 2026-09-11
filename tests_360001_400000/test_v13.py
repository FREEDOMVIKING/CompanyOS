import tempfile,unittest
from pathlib import Path
from companyos.customer_growth_crm_v13.engine import CRM,wj
class T(unittest.TestCase):
 def test_customer(self):
  with tempfile.TemporaryDirectory() as d:
   h=Path(d);sf=h/'companyos_runtime/storefront_sales_v8_190001_220000';sf.mkdir(parents=True)
   wj(sf/'orders.json',{'orders':[{'order_id':'o1','email':'buyer@example.com','product_id':'p1','status':'DELIVERED','amount_usd':59}]});wj(sf/'catalog.json',{'products':[{'product_id':'p2','name':'P2','score':90,'quality_passed':True,'pricing':{'recommended':34}}]})
   e=CRM(h);s=e.cycle();self.assertEqual(s['customers_total'],1);self.assertEqual(s['paying_customers'],1)
if __name__=='__main__':unittest.main()
