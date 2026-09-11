import json,tempfile,unittest
from pathlib import Path
from companyos.connectors_live.registry import build_registry
from companyos.connectors_live.engine import ConnectorEngine
from companyos.connectors_live.adapters import SMTPConnector, RESTConnector

class Tests(unittest.TestCase):
    def test_registry_has_eight_connectors(self):
        r=build_registry({})
        self.assertEqual(len(r),8)

    def test_disabled_connector(self):
        c=RESTConnector({'enabled':False})
        self.assertEqual(c.execute('x',{})['status'],'disabled')

    def test_dry_run(self):
        import os
        os.environ['TEST_API_URL']='https://example.com'
        c=RESTConnector({'enabled':True,'dry_run':True,'base_url_env':'TEST_API_URL'})
        self.assertEqual(c.execute('x',{'a':1})['status'],'dry_run')

    def test_queue_requires_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);(home/'config').mkdir()
            (home/'config'/'connectors.json').write_text('{}')
            e=ConnectorEngine(home)
            a=e.queue('smtp','send_email',{'to':'x'},'high')
            self.assertTrue(a['approval_required'])
            self.assertEqual(e.execute(a['action_id'])['status'],'approval_required')

    def test_approve_then_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);(home/'config').mkdir()
            (home/'config'/'connectors.json').write_text('{}')
            e=ConnectorEngine(home)
            a=e.queue('smtp','send_email',{'to':'x'},'high')
            e.approve(a['action_id'])
            self.assertEqual(e.execute(a['action_id'])['status'],'disabled')

    def test_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);(home/'config').mkdir()
            (home/'config'/'connectors.json').write_text('{}')
            r=ConnectorEngine(home).health()
            self.assertEqual(r['phase'],'21001-22000')
            self.assertEqual(len(r['connectors']),8)

    def test_demo_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);(home/'config').mkdir()
            (home/'config'/'connectors.json').write_text('{}')
            r=ConnectorEngine(home).demo_workflow()
            self.assertEqual(len(r['steps']),3)

if __name__=='__main__':
    unittest.main()
