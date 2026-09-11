from pathlib import Path
from datetime import datetime,timezone
import os,uuid
from .core import read_json,write_json,append_json,redact,policy,APIClient
class APIBackboneEngine:
 def __init__(self,home=None):
  self.home=Path(home or os.environ.get('COMPANYOS_HOME',str(Path.home()/'companyos')));self.runtime=self.home/'companyos_runtime'/'api_backbone';self.runtime.mkdir(parents=True,exist_ok=True);self.config=read_json(self.home/'config'/'api_profiles.json',{'profiles':{}});self.clients={k:APIClient(v) for k,v in self.config.get('profiles',{}).items()}
 def health(self):
  profiles={k:{'enabled':bool(c.p.get('enabled')),'configured':c.configured(),'dry_run':bool(c.p.get('dry_run',True)),'base_url':c.p.get('base_url'),'circuit':c.circuit.status()} for k,c in self.clients.items()};out={'phase':'22001-23000','generated_at':datetime.now(timezone.utc).isoformat(),'profile_count':len(profiles),'profiles':profiles};write_json(self.runtime/'health.json',out);return out
 def queue(self,profile,method,path,payload=None,query=None):
  pol=policy(method,path,payload,self.config.get('profiles',{}).get(profile,{}));job={'job_id':str(uuid.uuid4()),'profile':profile,'method':method.upper(),'path':path,'payload':payload,'query':query,**pol,'status':'queued','created_at':datetime.now(timezone.utc).isoformat()};append_json(self.runtime/'jobs.json',redact(job));return job
 def approve(self,job_id,approved_by='owner'):
  rec={'job_id':job_id,'approved':True,'approved_by':approved_by,'timestamp':datetime.now(timezone.utc).isoformat()};append_json(self.runtime/'approvals.json',rec);return rec
 def execute(self,job):
  if isinstance(job,str):job=next((x for x in read_json(self.runtime/'jobs.json',[]) if x.get('job_id')==job),None)
  if not job:return {'ok':False,'status':'job_not_found'}
  approved=any(x.get('job_id')==job['job_id'] and x.get('approved') for x in read_json(self.runtime/'approvals.json',[]))
  if job.get('approval_required') and not approved:return {'ok':False,'status':'approval_required','job_id':job['job_id']}
  c=self.clients.get(job['profile'])
  if not c:return {'ok':False,'status':'profile_not_found'}
  result=c.execute(job['method'],job['path'],job.get('payload'),job.get('query'));append_json(self.runtime/'executions.json',{'job':redact(job),'result':redact(result),'timestamp':datetime.now(timezone.utc).isoformat()});return result
 def demo(self):
  j=self.queue('example_readonly','GET','status',query={'source':'companyos'});return {'job':j,'result':self.execute(j)}
