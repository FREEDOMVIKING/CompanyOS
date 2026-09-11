import tempfile,unittest
from pathlib import Path
from companyos.venture_builder.engine import VentureBuilderEngine,product_spec,architecture_spec,slugify
from companyos.venture_builder.storage import write_json
class T(unittest.TestCase):
 def sample(self):
  return {"opportunity_id":"o1","title":"AI Estimating","business_plan":{"problem":"Slow estimates","customer":"contractors","recommended_product":{"name":"Estimate Assistant","type":"software_service","mvp":["intake","estimate","report"]}},"pricing":{"entry":49,"core":99,"premium":199},"forecast":{"monthly_revenue":1000,"monthly_profit":400}}
 def test_spec(self):self.assertEqual(product_spec(self.sample())["name"],"Estimate Assistant")
 def test_arch(self):self.assertIn("billing_interface",architecture_spec(product_spec(self.sample()))["modules"])
 def test_slug(self):self.assertEqual(slugify("AI Estimating!"),"ai-estimating")
 def test_full(self):
  with tempfile.TemporaryDirectory() as t:
   h=Path(t);d=h/"companyos_runtime"/"opportunity_engine";d.mkdir(parents=True);write_json(d/"ranking.json",[self.sample()])
   r=VentureBuilderEngine(h).build_top();p=Path(r["package_dir"])
   self.assertEqual(r["phase"],"25001-27000");self.assertTrue((p/"venture_manifest.json").exists());self.assertTrue((p/"website"/"index.html").exists());self.assertTrue((p/"saas_app"/"app.py").exists());self.assertTrue((p/"mobile_pwa"/"manifest.json").exists())
 def test_health(self):
  with tempfile.TemporaryDirectory() as t:self.assertEqual(VentureBuilderEngine(Path(t)).health()["build_count"],0)
if __name__=="__main__":unittest.main()
