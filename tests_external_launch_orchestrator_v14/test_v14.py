import tempfile,unittest
from pathlib import Path
from companyos.external_launch_orchestrator_v14.core import ExternalLaunchOrchestratorV14,now

class T(unittest.TestCase):
    def test_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); ws=h/"build"; ws.mkdir()
            files=[]
            for n in ("site.html","product.json","marketing.json","support.json"):
                p=ws/n; p.write_text("{}"); files.append(p)
            c=ExternalLaunchOrchestratorV14(h)
            c.exec("INSERT INTO company_builds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",("b","l","c","Test Venture","LOCALLY_BUILT",str(ws),str(files[0]),str(files[1]),str(files[2]),str(files[3]),"{}",now()))
            c.exec("INSERT INTO products VALUES(?,?,?,?,?,?,?,?)",("p","c","Core Offer","digital","READY",49,"{}",now()))
            c.exec("INSERT INTO campaigns VALUES(?,?,?,?,?,?,?,?)",("m","c","Launch","multi","DRAFT","Hello","{}",now()))
            s=c.cycle()["status"]
            self.assertEqual(s["launch_ready_total"],1); self.assertEqual(s["deployment_manifests_total"],1)
            self.assertEqual(s["domain_suggestions_total"],3); self.assertEqual(s["external_actions_review_required"],5)
            self.assertFalse(s["automatic_external_publish"]); self.assertFalse(s["automatic_spending"])
if __name__=="__main__": unittest.main()
