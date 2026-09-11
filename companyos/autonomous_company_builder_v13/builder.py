import json
from pathlib import Path
from .util import sid, now, slugify

class CompanyBuilder:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.generated=self.home/"generated_companies_v13"
        self.generated.mkdir(parents=True,exist_ok=True)

    def board_select(self):
        n=0
        for h in self.db.rows("SELECT * FROM venture_handoffs"):
            priority=88 if h["status"]=="READY_FOR_COMPANY_CREATION_REVIEW" else 72
            board_score=priority
            recommendation="APPROVE_INTERNAL_BUILD" if board_score>=80 else "HOLD_FOR_MORE_VALIDATION"
            lid=sid("launch_queue",h["handoff_id"])
            self.db.exec("""INSERT OR REPLACE INTO launch_queue
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (lid,h["handoff_id"],h["company_name"],
             "APPROVED_FOR_INTERNAL_BUILD" if recommendation=="APPROVE_INTERNAL_BUILD" else "HOLD",
             priority,board_score,recommendation,
             json.dumps({"external_launch":False,"financial_actions":False}),now()))
            n+=1
        return n

    def _write_site(self,folder,name,offer):
        site=folder/"website"
        site.mkdir(parents=True,exist_ok=True)
        html=f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title><style>body{{font-family:system-ui;max-width:900px;margin:40px auto;padding:20px}}
.hero{{padding:40px;border-radius:18px;background:#f2f4f8}}</style></head>
<body><div class="hero"><h1>{name}</h1><p>{offer}</p><p><strong>Status:</strong> locally generated launch preview</p></div></body></html>"""
        (site/"index.html").write_text(html,encoding="utf-8")
        return site/"index.html"

    def _write_json(self,path,data):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data,indent=2),encoding="utf-8")
        return path

    def build_companies(self):
        n=0
        existing={r["launch_id"] for r in self.db.rows("SELECT launch_id FROM company_builds")}
        for q in self.db.rows("SELECT * FROM launch_queue WHERE status='APPROVED_FOR_INTERNAL_BUILD' ORDER BY priority DESC"):
            if q["launch_id"] in existing: continue
            company_name=q["company_name"]
            slug=slugify(company_name)
            company_id=sid("v13-company",q["launch_id"])
            folder=self.generated/slug
            folder.mkdir(parents=True,exist_ok=True)

            offer=f"A focused solution from {company_name}, built around a validated customer problem."
            website=self._write_site(folder,company_name,offer)

            product=self._write_json(folder/"product"/"product.json",{
                "name":f"{company_name} Core Offer",
                "type":"productized_service_or_digital_product",
                "status":"READY_FOR_INTERNAL_REVIEW",
                "price_hint":49,
                "offer":offer
            })
            marketing=self._write_json(folder/"marketing"/"campaign.json",{
                "campaign":"Launch Validation",
                "channels":["email","social","direct_outreach"],
                "message":f"{company_name} helps a specific customer segment solve a recurring problem faster.",
                "automatic_posting":False
            })
            support=self._write_json(folder/"support"/"support.json",{
                "faq":[
                    {"q":"What does this company offer?","a":offer},
                    {"q":"How do I get started?","a":"Use the controlled pilot onboarding flow."}
                ],
                "automatic_external_messages":False
            })

            bid=sid("build",q["launch_id"])
            self.db.exec("""INSERT OR REPLACE INTO company_builds
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bid,q["launch_id"],company_id,company_name,"LOCALLY_BUILT",
             str(folder),str(website),str(product),str(marketing),str(support),
             json.dumps({"external_publish":False}),now()))

            self.db.exec("INSERT OR REPLACE INTO products VALUES(?,?,?,?,?,?,?,?)",
                         (sid("product",company_id),company_id,f"{company_name} Core Offer",
                          "productized_service_or_digital_product","READY_FOR_INTERNAL_REVIEW",49.0,
                          json.dumps({"workspace":str(folder)}),now()))

            self.db.exec("INSERT OR REPLACE INTO campaigns VALUES(?,?,?,?,?,?,?,?)",
                         (sid("campaign",company_id),company_id,"Launch Validation","multi-channel",
                          "DRAFT_READY",f"{company_name} helps a specific customer segment solve a recurring problem faster.",
                          json.dumps({"automatic_posting":False}),now()))

            self.db.exec("INSERT OR REPLACE INTO sales_plans VALUES(?,?,?,?,?,?,?,?)",
                         (sid("sales",company_id),company_id,"READY","narrow early-adopter niche",
                          offer,"direct outreach -> pilot -> referral -> inbound",
                          json.dumps({"automatic_outreach":False}),now()))

            self.db.exec("INSERT OR REPLACE INTO support_assets VALUES(?,?,?,?,?,?,?)",
                         (sid("support",company_id),company_id,"READY",
                          json.dumps([{"q":"What do you offer?","a":offer}]),
                          "Welcome. This is a controlled pilot onboarding package.",
                          json.dumps({"automatic_external_messages":False}),now()))

            self.db.exec("INSERT OR REPLACE INTO lifecycle VALUES(?,?,?,?,?,?,?)",
                         (company_id,"BUILD_COMPLETE",75.0,95.0,
                          "RUN_CONTROLLED_VALIDATION",
                          json.dumps({"external_launch":False}),now()))

            self.db.event("company.built","company_builder",{"company_id":company_id,"company_name":company_name})
            n+=1
        return n

    def lifecycle_refresh(self):
        n=0
        for b in self.db.rows("SELECT * FROM company_builds"):
            rev=self.db.rows("SELECT COALESCE(SUM(amount),0) AS total FROM revenue_ledger WHERE company_id=? AND verified=1",(b["company_id"],))[0]["total"]
            growth=75.0 if float(rev or 0)<=0 else min(100,75+float(rev)/100)
            next_action="RUN_CONTROLLED_VALIDATION" if float(rev or 0)<=0 else "OPTIMIZE_AND_SCALE"
            self.db.exec("""INSERT OR REPLACE INTO lifecycle VALUES(?,?,?,?,?,?,?)""",
                         (b["company_id"],"BUILD_COMPLETE" if float(rev or 0)<=0 else "EARLY_REVENUE",
                          growth,95.0,next_action,json.dumps({"verified_revenue":rev}),now()))
            n+=1
        return n

    def reinvestment_refresh(self):
        n=0
        rows=self.db.rows("""SELECT l.*,c.company_name FROM lifecycle l
                            JOIN company_builds c ON c.company_id=l.company_id
                            ORDER BY l.growth_score DESC""")
        for rank,r in enumerate(rows,1):
            score=float(r["growth_score"] or 0)
            rid=sid("reinvest",r["company_id"])
            rec="PRIORITIZE_FOR_INTERNAL_RESOURCES" if score>=80 else "VALIDATE_BEFORE_MORE_RESOURCES"
            self.db.exec("""INSERT OR REPLACE INTO reinvestment_recommendations
            VALUES(?,?,?,?,?,?,?,?)""",
                         (rid,r["company_id"],max(1,101-rank),score,rec,"RECOMMENDATION_ONLY",
                          json.dumps({"automatic_capital_transfer":False}),now()))
            n+=1
        return n
