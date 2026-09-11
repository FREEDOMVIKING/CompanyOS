import tempfile, unittest
from pathlib import Path
from companyos.autonomous_sales_marketing_v12.engine import Engine, write_json
class T(unittest.TestCase):
    def test_assets(self):
        with tempfile.TemporaryDirectory() as d:
            h=Path(d); sf=h/'companyos_runtime/storefront_sales_v8_190001_220000'; sf.mkdir(parents=True)
            write_json(sf/'catalog.json',{'products':[{'product_id':'test-kit','name':'Test Kit','score':92,'quality_passed':True,'pricing':{'recommended':39}}]}); write_json(sf/'orders.json',{'orders':[]})
            s=Engine(h).run(); self.assertEqual(s['campaigns_ready'],1); self.assertTrue((h/'marketing_assets_v12/test-kit/seo.json').exists()); self.assertFalse(s['external_publish_enabled'])
if __name__=='__main__': unittest.main()
