import base64,json,os,tempfile,time
from pathlib import Path
from urllib import request
from urllib.parse import urlencode
from collections import deque
SENSITIVE={"authorization","api_key","apikey","token","access_token","refresh_token","password","secret","client_secret","private_key"}
SAFE={"GET","HEAD","OPTIONS"}
RISKY={"purchase","buy","transfer","delete","deploy","publish","send","charge","withdraw","sign"}
def read_json(path,default):
 try:return json.loads(Path(path).read_text())
 except Exception:return default
def write_json(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=path.name+'.')
 try:
  with os.fdopen(fd,'w') as f:
   json.dump(data,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def append_json(path,item,limit=10000):
 rows=read_json(path,[]);rows=rows if isinstance(rows,list) else [];rows.append(item);write_json(path,rows[-limit:])
def redact(v):
 if isinstance(v,dict):return {k:('***REDACTED***' if str(k).lower() in SENSITIVE else redact(x)) for k,x in v.items()}
 if isinstance(v,list):return [redact(x) for x in v]
 return v
def policy(method,path,payload,profile):
 method=method.upper();txt=(path+' '+str(payload)).lower();risky=method not in SAFE or any(x in txt for x in RISKY);req=risky and not bool(profile.get('read_only',False));return {'approval_required':req,'execution_mode':'proposal_only' if req else 'auto','risk':'high' if req else 'low'}
def auth_headers(auth):
 auth=auth or {'type':'none'};typ=auth.get('type','none')
 if typ=='none':return {}
 if typ in {'bearer','oauth2'}:
  t=os.environ.get(auth.get('token_env',''),'');return {'Authorization':f'Bearer {t}'} if t else {}
 if typ=='api_key':
  k=os.environ.get(auth.get('key_env',''),'');return {auth.get('header','X-API-Key'):k} if k else {}
 if typ=='basic':
  u=os.environ.get(auth.get('username_env',''),'');p=os.environ.get(auth.get('password_env',''),'');return {'Authorization':'Basic '+base64.b64encode(f'{u}:{p}'.encode()).decode()} if u and p else {}
 return {}
class RateLimiter:
 def __init__(self,n):self.n=max(1,int(n or 60));self.calls=deque()
 def allow(self):
  now=time.time()
  while self.calls and now-self.calls[0]>=60:self.calls.popleft()
  if len(self.calls)>=self.n:return False
  self.calls.append(now);return True
class Circuit:
 def __init__(self,threshold=5,cooldown=60):self.threshold=threshold;self.cooldown=cooldown;self.failures=0;self.opened=None
 def allow(self):
  if self.opened is None:return True
  if time.time()-self.opened>=self.cooldown:self.failures=0;self.opened=None;return True
  return False
 def ok(self):self.failures=0;self.opened=None
 def fail(self):
  self.failures+=1
  if self.failures>=self.threshold:self.opened=time.time()
 def status(self):return {'open':self.opened is not None,'failures':self.failures}
class APIClient:
 def __init__(self,p):self.p=p;self.base=p.get('base_url','').rstrip('/');self.timeout=int(p.get('timeout_seconds',20));self.retries=int(p.get('max_retries',2));self.limiter=RateLimiter(p.get('rate_limit_per_minute',60));self.circuit=Circuit()
 def configured(self):return bool(self.p.get('enabled')) and bool(self.base)
 def execute(self,method,path,payload=None,query=None):
  method=method.upper()
  if method not in self.p.get('allowed_methods',['GET']):return {'ok':False,'status':'method_not_allowed'}
  if not self.configured():return {'ok':False,'status':'profile_not_configured'}
  if not self.circuit.allow():return {'ok':False,'status':'circuit_open'}
  if not self.limiter.allow():return {'ok':False,'status':'rate_limited'}
  url=self.base+'/'+path.lstrip('/')
  if query:url+='?'+urlencode(query)
  if self.p.get('dry_run',True):return {'ok':True,'status':'dry_run','method':method,'url':url,'payload':payload}
  body=None if payload is None else json.dumps(payload).encode();headers={'Content-Type':'application/json',**auth_headers(self.p.get('auth'))};last=None
  for i in range(self.retries+1):
   try:
    req=request.Request(url,data=body,headers=headers,method=method)
    with request.urlopen(req,timeout=self.timeout) as resp:
     raw=resp.read().decode();self.circuit.ok();return {'ok':True,'status':'success','status_code':resp.status,'body':json.loads(raw) if raw else {}}
   except Exception as e:
    last=e;self.circuit.fail()
    if i<self.retries:time.sleep(min(2**i,4))
  return {'ok':False,'status':'request_failed','error':str(last)}
