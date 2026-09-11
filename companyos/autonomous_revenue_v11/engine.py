import json,os,smtplib,tempfile,urllib.request
from datetime import datetime,timezone
from email.message import EmailMessage
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def rj(p,d=None):
    try:return json.loads(Path(p).read_text())
    except:return {} if d is None else d
def wj(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+".")
    with os.fdopen(fd,"w") as f: json.dump(d,f,indent=2,default=str);f.flush();os.fsync(f.fileno())
    os.replace(t,p)
def aj(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a") as f:f.write(json.dumps(d,default=str)+"\n")
def gj(url):
    with urllib.request.urlopen(url,timeout=6) as x:return json.loads(x.read())

class Engine:
    def __init__(self,home):
        self.h=Path(home);self.live=self.h/".companyos_runtime"
        self.rt=self.h/"companyos_runtime/autonomous_revenue_v11_280001_320000"
        self.sf=self.h/"companyos_runtime/storefront_sales_v8_190001_220000"
        self.pay=self.h/"companyos_runtime/crypto_payment_bridge_v9_220001_250000"
        self.prod=self.h/"generated_products_v7";self.pack=self.h/"storefront_v8_fulfillment"
        self.deliv=self.h/"delivery_records_v11"
        for p in (self.live,self.rt,self.sf,self.deliv):p.mkdir(parents=True,exist_ok=True)

    def products(self):
        out=[]
        if not self.prod.exists():return out
        for m in self.prod.glob("*/product_manifest.json"):
            x=rj(m,{});v=rj(m.parent/"validation_report.json",{})
            if not x or not v.get("passed"):continue
            pid=x.get("product_id",m.parent.name);z=self.pack/f"{pid}.zip"
            out.append({"product_id":pid,"name":x.get("name",pid),"score":x.get("score",0),
              "pricing":x.get("pricing",{}),"workspace":str(m.parent),"quality_passed":True,
              "state":v.get("state","READY"),"fulfillment_package":str(z) if z.exists() else None})
        return out

    def sync(self):
        c=rj(self.sf/"catalog.json",{"products":[]});by={p.get("product_id"):p for p in c.get("products",[])}
        added=updated=0
        for p in self.products():
            if p["product_id"] not in by:by[p["product_id"]]={**p,"checkout_enabled":True};added+=1
            else:
                old=dict(by[p["product_id"]]);by[p["product_id"]].update(p)
                updated+=old!=by[p["product_id"]]
        c["products"]=sorted(by.values(),key=lambda x:x.get("score",0),reverse=True);c["generated_at"]=now()
        wj(self.sf/"catalog.json",c);return {"products_total":len(c["products"]),"added":added,"updated":updated}

    def invoices(self):
        try:return gj("http://127.0.0.1:8771/api/invoices")
        except:return rj(self.pay/"invoices.json",{"invoices":[]})

    def orders(self):return rj(self.sf/"orders.json",{"orders":[]})

    def smtp_ready(self):
        return all(os.getenv(k) for k in ("SMTP_HOST","SMTP_PORT","SMTP_USERNAME","SMTP_PASSWORD","SMTP_FROM"))

    def sendmail(self,rec):
        z=Path(rec["fulfillment_package"])
        msg=EmailMessage();msg["Subject"]="Your CompanyOS purchase";msg["From"]=os.environ["SMTP_FROM"];msg["To"]=rec["email"]
        msg.set_content(f"Thank you. Order: {rec['order_id']}")
        msg.add_attachment(z.read_bytes(),maintype="application",subtype="zip",filename=z.name)
        with smtplib.SMTP(os.environ["SMTP_HOST"],int(os.environ["SMTP_PORT"]),timeout=20) as s:
            s.starttls();s.login(os.environ["SMTP_USERNAME"],os.environ["SMTP_PASSWORD"]);s.send_message(msg)

    def fulfill(self):
        inv={x.get("order_id"):x for x in self.invoices().get("invoices",[]) if str(x.get("status")).upper()=="PAID"}
        o=self.orders();idx=rj(self.rt/"delivery_index.json",{"orders":{}});new=sent=0
        for order in o.get("orders",[]):
            oid=order.get("order_id")
            if oid not in inv or oid in idx["orders"]:continue
            i=inv[oid];rec={"order_id":oid,"invoice_id":i.get("invoice_id"),"product_id":order.get("product_id"),
              "email":order.get("email"),"transaction_id":i.get("transaction_id"),
              "fulfillment_package":order.get("fulfillment_package") or i.get("fulfillment_package"),
              "status":"READY_FOR_DELIVERY","email_sent":False,"created_at":now()}
            f=self.deliv/f"{oid}.json";wj(f,rec);aj(self.rt/"fulfillment_queue.jsonl",rec);new+=1
            if self.smtp_ready() and rec.get("email") and rec.get("fulfillment_package"):
                try:self.sendmail(rec);rec["email_sent"]=True;rec["status"]="DELIVERED";rec["delivered_at"]=now();sent+=1;wj(f,rec)
                except Exception as e:rec["email_error"]=str(e);wj(f,rec)
            idx["orders"][oid]=rec;order["status"]="DELIVERED" if rec["email_sent"] else "FULFILLMENT_READY";order["delivery_record"]=str(f)
        wj(self.rt/"delivery_index.json",idx);wj(self.sf/"orders.json",o)
        return {"new_records":new,"emails_sent":sent,"records_total":len(idx["orders"])}

    def analytics(self):
        o=self.orders().get("orders",[]);paid=[x for x in o if x.get("status") in ("PAID","FULFILLMENT_READY","DELIVERED")]
        return {"orders_total":len(o),"paid_or_beyond":len(paid),"delivered":sum(x.get("status")=="DELIVERED" for x in o),
          "revenue_usd":round(sum(float(x.get("amount_usd",0) or 0) for x in paid),2),"updated_at":now()}

    def cycle(self):
        s={"status":"autonomous_revenue_pipeline_ready","catalog_sync":self.sync(),"fulfillment":self.fulfill(),
           "smtp_delivery_enabled":self.smtp_ready(),"analytics":self.analytics(),
           "storefront_url":"http://127.0.0.1:8772","updated_at":now()}
        wj(self.live/"autonomous_revenue_v11_live.json",s);aj(self.live/"full_autonomy_journal.jsonl",
          {"ts":now(),"event":"autonomous_revenue_v11_cycle","event_type":"autonomous_revenue_v11_cycle","state":s})
        return s
