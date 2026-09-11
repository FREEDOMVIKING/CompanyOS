import json, sqlite3, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone
def now(): return datetime.now(timezone.utc).isoformat()
def sid(*x): return hashlib.sha256('|'.join(map(str,x)).encode()).hexdigest()[:24]
SCHEMA='''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS company_builds(build_id TEXT PRIMARY KEY,launch_id TEXT,company_id TEXT,company_name TEXT,status TEXT,workspace_path TEXT,website_path TEXT,product_path TEXT,marketing_path TEXT,support_path TEXT,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS connectors(name TEXT PRIMARY KEY,category TEXT,status TEXT,mode TEXT,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS action_queue(action_id TEXT PRIMARY KEY,company_id TEXT,action_type TEXT,status TEXT,risk_level TEXT,connector_name TEXT,description TEXT,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS receipts(receipt_id TEXT PRIMARY KEY,action_id TEXT,company_id TEXT,connector_name TEXT,status TEXT,external_ref TEXT,response_json TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT,company_id TEXT,actor TEXT,decision TEXT,payload_json TEXT,created_at TEXT);
'''
class ExternalIntegrationExecutionV15:
 def __init__(self,home):
  self.home=Path(home); self.run=self.home/'.companyos_enterprise_v15'; self.run.mkdir(parents=True,exist_ok=True); self.db=self.run/'companyos_enterprise_v15.sqlite3'
  c=sqlite3.connect(self.db); c.executescript(SCHEMA); c.commit(); c.close()
  self.cfg=self.home/'config/connectors_v15.json'; self.cfg.parent.mkdir(parents=True,exist_ok=True)
  if not self.cfg.exists(): self.cfg.write_text(json.dumps({'static_host':{'enabled':True,'mode':'local_publish','publish_root':'~/companyos/published_sites_v15'},'analytics':{'enabled':True,'mode':'local_event_log'},'dns_provider':{'enabled':False,'mode':'disabled'},'storefront':{'enabled':False,'mode':'disabled'},'email_outreach':{'enabled':False,'mode':'disabled'},'domain_registrar':{'enabled':False,'mode':'disabled'}},indent=2),encoding='utf-8')
 def rows(self,sql,args=()):
  c=sqlite3.connect(self.db); c.row_factory=sqlite3.Row
  try:return [dict(r) for r in c.execute(sql,args).fetchall()]
  finally:c.close()
 def exec(self,sql,args=()):
  c=sqlite3.connect(self.db)
  try:c.execute(sql,args); c.commit()
  finally:c.close()
 def audit(self,e,cid,actor,decision,payload): self.exec('INSERT INTO audit(event_type,company_id,actor,decision,payload_json,created_at) VALUES(?,?,?,?,?,?)',(e,cid,actor,decision,json.dumps(payload),now()))
 def migrate(self):
  src=self.home/'.companyos_enterprise_v14/companyos_enterprise_v14.sqlite3'; counts={'company_builds':0,'actions':0}
  if not src.exists(): return {'status':'no_v14_database','counts':counts}
  c=sqlite3.connect(src); c.row_factory=sqlite3.Row
  try:
   try: builds=[dict(r) for r in c.execute('SELECT * FROM company_builds')]
   except Exception: builds=[]
   for d in builds:
    self.exec('INSERT OR REPLACE INTO company_builds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(d['build_id'],d['launch_id'],d['company_id'],d['company_name'],d['status'],d['workspace_path'],d['website_path'],d['product_path'],d['marketing_path'],d['support_path'],d.get('payload_json') or '{}',now())); counts['company_builds']+=1
   rows=[]
   for table in ('action_queue','external_action_queue'):
    try: rows=[dict(r) for r in c.execute(f'SELECT * FROM {table}')]
    except Exception: rows=[]
    if rows: break
   for d in rows:
    aid=d.get('id') or d.get('action_id'); self.exec('INSERT OR REPLACE INTO action_queue VALUES(?,?,?,?,?,?,?,?,?)',(aid,d['company_id'],d['action_type'],d.get('status','REVIEW_REQUIRED'),d.get('risk') or d.get('risk_level') or 'MEDIUM',d.get('connector') or d.get('connector_name') or '',d.get('description') or '',d.get('payload_json') or '{}',now())); counts['actions']+=1
  finally:c.close()
  return {'status':'migration_complete','counts':counts}
 def sync_connectors(self):
  cfg=json.loads(self.cfg.read_text()); cats={'static_host':'hosting','analytics':'analytics','dns_provider':'dns','storefront':'commerce','email_outreach':'marketing','domain_registrar':'domain'}
  for name,d in cfg.items():
   status='HEALTHY' if d.get('enabled') and ((name=='static_host' and d.get('mode')=='local_publish') or (name=='analytics' and d.get('mode')=='local_event_log')) else ('CONFIGURED' if d.get('enabled') else 'DISABLED')
   self.exec('INSERT OR REPLACE INTO connectors VALUES(?,?,?,?,?,?)',(name,cats.get(name,'integration'),status,d.get('mode','disabled'),json.dumps(d),now()))
  return len(cfg)
 def approve(self,action_id):
  rs=self.rows('SELECT * FROM action_queue WHERE action_id=?',(action_id,))
  if not rs:return {'ok':False,'error':'action_not_found'}
  a=rs[0]
  if a['action_type'] in {'PURCHASE_DOMAIN','WALLET_SIGN','FUND_TRANSFER','SPEND'}: return {'ok':False,'error':'financial_or_irreversible_action_blocked'}
  self.exec("UPDATE action_queue SET status='APPROVED',updated_at=? WHERE action_id=?",(now(),action_id)); self.audit('action.approved',a['company_id'],'control_plane','APPROVED',{'action_id':action_id}); return {'ok':True,'action_id':action_id}
 def execute(self):
  cfg=json.loads(self.cfg.read_text()); executed=failed=0
  for a in self.rows("SELECT * FROM action_queue WHERE status='APPROVED'"):
   if a['action_type']=='PUBLISH_STATIC_SITE' and cfg.get('static_host',{}).get('enabled') and cfg['static_host'].get('mode')=='local_publish':
    b=self.rows('SELECT * FROM company_builds WHERE company_id=?',(a['company_id'],))
    if b and Path(b[0]['website_path']).exists():
     root=Path(cfg['static_host'].get('publish_root','~/companyos/published_sites_v15')).expanduser(); dest=root/a['company_id']; dest.mkdir(parents=True,exist_ok=True); target=dest/'index.html'; shutil.copy2(b[0]['website_path'],target); status='EXECUTED'; ref=str(target); result={'ok':True,'external_ref':ref}; executed+=1
    else: status='FAILED'; ref=None; result={'ok':False,'error':'site_missing'}; failed+=1
   else: status='REVIEW_ONLY'; ref=None; result={'ok':False,'error':'connector_write_not_enabled'}; failed+=1
   self.exec('INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)',(sid('receipt',a['action_id'],now()),a['action_id'],a['company_id'],a['connector_name'],status,ref,json.dumps(result),now())); self.exec('UPDATE action_queue SET status=?,updated_at=? WHERE action_id=?',(status,now(),a['action_id'])); self.audit('action.execution',a['company_id'],'v15_executor',status,{'action_id':a['action_id'],'result':result})
  return {'executed':executed,'failed':failed}
 def cycle(self): return {'migration':self.migrate(),'connectors_synced':self.sync_connectors(),'execution':self.execute(),'status':self.status()}
 def status(self):
  con=self.rows('SELECT * FROM connectors'); acts=self.rows('SELECT * FROM action_queue')
  return {'status':'companyos_external_integration_execution_v15_ready','external_integration_execution':'ONLINE','company_builds_total':len(self.rows('SELECT * FROM company_builds')),'connectors_total':len(con),'connectors_configured':sum(x['status'] in ('CONFIGURED','HEALTHY') for x in con),'connectors_healthy':sum(x['status']=='HEALTHY' for x in con),'actions_total':len(acts),'actions_review_required':sum(x['status']=='REVIEW_REQUIRED' for x in acts),'actions_approved':sum(x['status']=='APPROVED' for x in acts),'actions_executed':sum(x['status']=='EXECUTED' for x in acts),'execution_receipts_total':len(self.rows('SELECT * FROM receipts')),'automatic_financial_execution':False,'automatic_wallet_signing':False,'automatic_fund_transfers':False,'automatic_domain_purchase':False,'dashboard_url':'http://127.0.0.1:9000','updated_at':now()}
