import tempfile,unittest
from pathlib import Path
from companyos.external_integration_execution_v15.core import ExternalIntegrationExecutionV15,now
class T(unittest.TestCase):
 def test_publish(self):
  with tempfile.TemporaryDirectory() as td:
   h=Path(td); site=h/'site.html'; site.write_text('<h1>x</h1>')
   c=ExternalIntegrationExecutionV15(h); c.exec('INSERT INTO company_builds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',('b','l','c','Test','LOCALLY_BUILT',str(h),str(site),str(site),str(site),str(site),'{}',now())); c.exec('INSERT INTO action_queue VALUES(?,?,?,?,?,?,?,?,?)',('a','c','PUBLISH_STATIC_SITE','REVIEW_REQUIRED','HIGH','static_host','Publish','{}',now())); c.sync_connectors(); self.assertTrue(c.approve('a')['ok']); self.assertEqual(c.execute()['executed'],1); self.assertEqual(c.status()['actions_executed'],1)
 def test_financial_block(self):
  with tempfile.TemporaryDirectory() as td:
   c=ExternalIntegrationExecutionV15(Path(td)); c.exec('INSERT INTO action_queue VALUES(?,?,?,?,?,?,?,?,?)',('a','c','PURCHASE_DOMAIN','REVIEW_REQUIRED','HIGH','domain_registrar','Buy','{}',now())); self.assertFalse(c.approve('a')['ok'])
if __name__=='__main__':unittest.main()
