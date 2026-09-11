import tempfile, unittest
from pathlib import Path
from companyos.action_control_execution_v16.core import ActionControlExecutionV16
from companyos.action_control_execution_v16.util import now

class T(unittest.TestCase):
    def test_publish(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); ws=h/"site"; ws.mkdir(); site=ws/"index.html"; site.write_text("<h1>Hello</h1>")
            c=ActionControlExecutionV16(h)
            c.db.exec("INSERT INTO company_builds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",("b","l","c1","Test","LOCALLY_BUILT",str(ws),str(site),str(site),str(site),str(site),"{}",now()))
            c.db.exec("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",("a1","c1","PUBLISH_STATIC_SITE","REVIEW_REQUIRED","HIGH","static_host","Publish","UNREVIEWED",0,None,None,"{}",now()))
            c.connectors.sync(); c.connectors.health()
            self.assertTrue(c.executor.approve("a1")["ok"])
            self.assertEqual(c.executor.execute()["executed"],1)
            s=c.status(); self.assertEqual(s["actions_executed"],1); self.assertEqual(s["receipts_total"],1)
    def test_financial_block(self):
        with tempfile.TemporaryDirectory() as td:
            c=ActionControlExecutionV16(Path(td))
            c.db.exec("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",("a2","c1","PURCHASE_DOMAIN","REVIEW_REQUIRED","HIGH","domain_registrar","Buy","UNREVIEWED",0,None,None,"{}",now()))
            c.executor.review_all()
            self.assertEqual(c.db.rows("SELECT * FROM actions")[0]["status"],"BLOCKED_POLICY")
            self.assertFalse(c.executor.approve("a2")["ok"])
    def test_retry_limit(self):
        with tempfile.TemporaryDirectory() as td:
            c=ActionControlExecutionV16(Path(td))
            c.db.exec("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",("a3","c1","POST_WEBHOOK","HTTP_ERROR","MEDIUM","webhook","Post","MANUAL_APPROVAL_REQUIRED",5,None,"x","{}",now()))
            self.assertFalse(c.executor.retry("a3")["ok"])
if __name__=="__main__": unittest.main()
