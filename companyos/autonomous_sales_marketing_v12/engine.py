import json, os, re, tempfile
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(path, default=None):
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception: return {} if default is None else default
def write_json(path, data):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.', dir=str(path.parent))
    with os.fdopen(fd,'w',encoding='utf-8') as f:
        json.dump(data,f,indent=2,sort_keys=True,default=str); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
def append_jsonl(path,row):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a',encoding='utf-8') as f: f.write(json.dumps(row,default=str)+'\n')
def slug(v): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',str(v).lower())).strip('-')

class Engine:
    def __init__(self, home):
        self.home=Path(home); self.live=self.home/'.companyos_runtime'
        self.runtime=self.home/'companyos_runtime/autonomous_sales_marketing_v12_320001_360000'
        self.storefront=self.home/'companyos_runtime/storefront_sales_v8_190001_220000'
        self.assets=self.home/'marketing_assets_v12'
        for p in (self.live,self.runtime,self.assets): p.mkdir(parents=True,exist_ok=True)
    def catalog(self): return read_json(self.storefront/'catalog.json', {'products':[]})
    def orders(self): return read_json(self.storefront/'orders.json', {'orders':[]}).get('orders',[])
    def metrics(self,pid):
        orders=[o for o in self.orders() if o.get('product_id')==pid]
        paid=[o for o in orders if o.get('status') in ('PAID','FULFILLMENT_READY','DELIVERED')]
        return {'orders':len(orders),'paid_orders':len(paid),'revenue_usd':round(sum(float(o.get('amount_usd',0) or 0) for o in paid),2)}
    def price(self,p):
        current=float(p.get('pricing',{}).get('recommended',0) or 0); m=self.metrics(p.get('product_id')); score=float(p.get('score',0) or 0)
        if current<=0: rec,reason=29.0,'No valid current price was found.'
        elif m['paid_orders']>=5: rec,reason=round(min(current*1.10,current+15),2),'Paid demand supports a bounded increase.'
        elif m['orders']>=5 and not m['paid_orders']: rec,reason=round(max(current*.90,5),2),'Checkout interest without conversion supports a bounded decrease test.'
        elif score>=90: rec,reason=round(min(current*1.05,current+8),2),'High product score supports a small premium test.'
        else: rec,reason=current,'Insufficient conversion evidence; hold price.'
        return {'current':current,'recommended':rec,'change_percent':round(((rec-current)/current)*100,2) if current else 0,'reason':reason,'auto_apply':False}
    def build(self,p):
        pid=p.get('product_id'); name=p.get('name',pid); price=p.get('pricing',{}).get('recommended',0)
        words=[x for x in re.findall(r'[A-Za-z0-9]+',name.lower()) if len(x)>2]
        keywords=list(dict.fromkeys(words+['digital download','business template','instant access']))[:10]
        folder=self.assets/slug(pid or name); folder.mkdir(parents=True,exist_ok=True)
        docs={
          'seo.json':{'seo_title':f'{name} | Instant Digital Download','meta_description':f'Get the {name}, a ready-to-use digital resource built to save time.','keywords':keywords,'cta':'Get instant access'},
          'social_campaign.json':{'short_post':f'Save time with the {name}. Available now for ${price}.','hashtags':['#'+slug(x).replace('-','') for x in keywords[:5]]},
          'marketplace_listing.json':{'title':name,'price':price,'summary':f'A ready-to-use {name}.','external_publish_status':'REVIEW_REQUIRED'},
          'email_campaign.json':{'subject':f'Save time with the {name}','body':f'The {name} is ready and available for ${price}.','cta':'View product'},
          'pricing_recommendation.json':self.price(p),
        }
        for fn,obj in docs.items(): write_json(folder/fn,obj)
        return {'product_id':pid,'name':name,'asset_folder':str(folder),'pricing':docs['pricing_recommendation.json'],'status':'MARKETING_ASSETS_READY_FOR_REVIEW'}
    def run(self):
        products=[p for p in self.catalog().get('products',[]) if p.get('quality_passed')]
        campaigns=[]
        for p in products:
            c=self.build(p); m=self.metrics(p.get('product_id'))
            c['priority_score']=round(float(p.get('score',0) or 0)+min(m['revenue_usd']/10,20)+min(m['paid_orders']*3,15),2)
            campaigns.append(c)
        campaigns.sort(key=lambda x:x['priority_score'],reverse=True)
        queue={'status':'CAMPAIGNS_READY_FOR_REVIEW','external_publish_enabled':False,'campaign_count':len(campaigns),'campaigns':campaigns,'updated_at':now()}
        write_json(self.runtime/'campaign_queue.json',queue)
        state={'status':'autonomous_sales_marketing_ready','products_analyzed':len(products),'campaigns_ready':len(campaigns),'external_publish_enabled':False,'pricing_auto_apply':False,'top_priority_product':campaigns[0]['product_id'] if campaigns else None,'dashboard_url':'http://127.0.0.1:8774','updated_at':now()}
        write_json(self.live/'autonomous_sales_marketing_v12_live.json',state)
        append_jsonl(self.live/'full_autonomy_journal.jsonl',{'ts':now(),'event':'autonomous_sales_marketing_v12_cycle','state':state})
        return state
    def queue(self): return read_json(self.runtime/'campaign_queue.json', {'campaigns':[]})
