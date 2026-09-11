import hashlib,json,os,re,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
def now():return datetime.now(timezone.utc).isoformat()
def rj(p,d=None):
 try:return json.loads(Path(p).read_text())
 except:return {} if d is None else d
def wj(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.')
 with os.fdopen(fd,'w') as f:json.dump(d,f,indent=2,default=str);f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def aj(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a') as f:f.write(json.dumps(d,default=str)+'\n')
def sid(v):return hashlib.sha256(str(v).encode()).hexdigest()[:16]
class CRM:
 def __init__(self,h):
  self.h=Path(h);self.live=self.h/'.companyos_runtime';self.rt=self.h/'companyos_runtime/customer_growth_crm_v13_360001_400000';self.sf=self.h/'companyos_runtime/storefront_sales_v8_190001_220000';self.rec=self.h/'crm_records_v13'
  [p.mkdir(parents=True,exist_ok=True) for p in (self.live,self.rt,self.rec)]
 def orders(self):return rj(self.sf/'orders.json',{'orders':[]}).get('orders',[])
 def catalog(self):return rj(self.sf/'catalog.json',{'products':[]}).get('products',[])
 def customers(self):
  x={}
  for o in self.orders():
   e=str(o.get('email') or '').strip().lower()
   if not e:continue
   k=sid(e);p=x.setdefault(k,{'customer_id':k,'email':e,'orders':[],'paid_orders':0,'lifetime_value_usd':0.0,'status':'LEAD'})
   p['orders'].append(o.get('order_id'))
   if o.get('status') in ('PAID','FULFILLMENT_READY','DELIVERED'):
    p['paid_orders']+=1;p['lifetime_value_usd']+=float(o.get('amount_usd',0) or 0);p['status']='CUSTOMER'
  for p in x.values():
   p['lifetime_value_usd']=round(p['lifetime_value_usd'],2);p['segment']='VIP' if p['lifetime_value_usd']>=200 else 'REPEAT' if p['paid_orders']>=2 else 'CUSTOMER' if p['paid_orders']==1 else 'LEAD';p['referral_code']='REF-'+p['customer_id'][:8].upper()
  return list(x.values())
 def recs(self,c):
  owned={o.get('product_id') for o in self.orders() if o.get('order_id') in set(c['orders']) and o.get('status') in ('PAID','FULFILLMENT_READY','DELIVERED')}
  ps=[p for p in self.catalog() if p.get('quality_passed') and p.get('product_id') not in owned];ps.sort(key=lambda p:float(p.get('score',0) or 0),reverse=True)
  return [{'product_id':p.get('product_id'),'name':p.get('name'),'price':p.get('pricing',{}).get('recommended')} for p in ps[:3]]
 def plan(self,c):
  base=datetime.now(timezone.utc);steps=[('INTRO',0),('VALUE_PROOF',2),('FINAL_REMINDER',5)] if c['segment']=='LEAD' else [('THANK_YOU',0),('REVIEW_REQUEST',3),('CROSS_SELL',7),('REFERRAL_INVITE',14)]
  return [{'step':n,'scheduled_for':(base+timedelta(days=d)).isoformat(),'send_status':'QUEUED_FOR_REVIEW'} for n,d in steps]
 def tickets(self):return rj(self.rt/'support_tickets.json',{'tickets':[]})
 def create_ticket(self,email,subject,message):
  d=self.tickets();t={'ticket_id':sid(email+subject+now()),'email':email,'subject':subject,'message':message,'priority':'HIGH' if re.search(r'\\b(refund|fraud|charged|cannot access|missing)\\b',message,re.I) else 'NORMAL','status':'OPEN','created_at':now()};d['tickets'].append(t);wj(self.rt/'support_tickets.json',d);return t
 def cycle(self):
  cs=self.customers();idx={}
  for c in cs:
   q={**c,'recommendations':self.recs(c),'follow_up_plan':self.plan(c),'external_email_enabled':False};idx[c['customer_id']]=q;wj(self.rec/(c['customer_id']+'.json'),q)
  hist=round(sum(c['lifetime_value_usd'] for c in cs),2);pay=sum(c['paid_orders']>0 for c in cs);leads=sum(c['segment']=='LEAD' for c in cs)
  s={'status':'customer_growth_crm_ready','customers_total':len(cs),'leads':leads,'paying_customers':pay,'vip_customers':sum(c['segment']=='VIP' for c in cs),'open_support_tickets':sum(t.get('status')=='OPEN' for t in self.tickets().get('tickets',[])),'external_email_enabled':False,'forecast':{'historical_revenue_usd':hist,'next_30_days':{'conservative':round(hist+pay*20+leads*5,2),'base':round(hist+pay*35+leads*12,2),'upside':round(hist+pay*60+leads*25,2)},'method':'bounded scenario model; not a guarantee'},'dashboard_url':'http://127.0.0.1:8775','updated_at':now()}
  wj(self.rt/'crm_index.json',{'customers':idx,'updated_at':now()});wj(self.live/'customer_growth_crm_v13_live.json',s);aj(self.live/'full_autonomy_journal.jsonl',{'ts':now(),'event':'customer_growth_crm_v13_cycle','state':s});return s
 def index(self):return rj(self.rt/'crm_index.json',{'customers':{}})
