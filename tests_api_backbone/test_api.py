import os,json,tempfile,unittest
from pathlib import Path
from companyos.api_backbone.core import redact,auth_headers,policy,APIClient
from companyos.api_backbone.engine import APIBackboneEngine
class T(unittest.TestCase):
 def test_redact(self):self.assertEqual(redact({'token':'x'})['token'],'***REDACTED***')
 def test_auth(self):os.environ['TOK']='abc';self.assertEqual(auth_headers({'type':'bearer','token_env':'TOK'})['Authorization'],'Bearer abc')
 def test_policy(self):self.assertFalse(policy('GET','items',None,{'read_only':True})['approval_required']);self.assertTrue(policy('POST','items',{}, {'read_only':False})['approval_required'])
 def test_dry(self):self.assertEqual(APIClient({'enabled':True,'base_url':'https://example.com','dry_run':True,'allowed_methods':['GET']}).execute('GET','status')['status'],'dry_run')
 def test_engine(self):
  with tempfile.TemporaryDirectory() as t:
   h=Path(t);(h/'config').mkdir();(h/'config'/'api_profiles.json').write_text(json.dumps({'profiles':{}}));self.assertEqual(APIBackboneEngine(h).health()['phase'],'22001-23000')
 def test_approval(self):
  with tempfile.TemporaryDirectory() as t:
   h=Path(t);(h/'config').mkdir();(h/'config'/'api_profiles.json').write_text(json.dumps({'profiles':{'p':{'enabled':True,'base_url':'https://example.com','dry_run':True,'allowed_methods':['POST'],'read_only':False}}}));e=APIBackboneEngine(h);j=e.queue('p','POST','items',{'x':1});self.assertEqual(e.execute(j)['status'],'approval_required');e.approve(j['job_id']);self.assertEqual(e.execute(j)['status'],'dry_run')
if __name__=='__main__':unittest.main()
