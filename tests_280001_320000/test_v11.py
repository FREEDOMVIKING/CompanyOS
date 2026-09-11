import tempfile,unittest
from pathlib import Path
from companyos.autonomous_revenue_v11.engine import Engine,wj
class T(unittest.TestCase):
 def test_sync(self):
  with tempfile.TemporaryDirectory() as d:
   h=Path(d);p=h/"generated_products_v7/x";p.mkdir(parents=True)
   wj(p/"product_manifest.json",{"product_id":"x","name":"X","score":90,"pricing":{"recommended":39}})
   wj(p/"validation_report.json",{"passed":True});(h/"storefront_v8_fulfillment").mkdir();(h/"storefront_v8_fulfillment/x.zip").write_bytes(b"x")
   e=Engine(h);self.assertEqual(e.sync()["added"],1)
if __name__=="__main__":unittest.main()
