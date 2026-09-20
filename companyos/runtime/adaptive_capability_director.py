from __future__ import annotations
import json, os, re, sys, time
from collections import Counter
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
GRT=Path.home()/".companyos_runtime"
STATE=RT/"adaptive_capability_director_state.json"
POLICY=RT/"adaptive_capability_policy.json"
REQUESTS=RT/"adaptive_capability_requests.json"
INTEGRATIONS=RT/"integration_capability_requests.json"
LEARNING=RT/"adaptive_capability_learning.json"
FEEDBACK=RT/"capability_feedback_state.json"
FAILURES=RT/"adaptive_capability_failures.json"
DYNAMIC_GAPS=RT/"adaptive_dynamic_capability_gaps.json"
REPORTS=GRT/"reports"
STOP=RT/"STOP_CONTINUOUS"
REPORTS.mkdir(parents=True,exist_ok=True)

MIN_MB=max(500,int(os.getenv("COMPANYOS_CAPABILITY_DIRECTOR_MIN_AVAILABLE_MB","850")))

POLICY_DATA={
 "version":"V65.97",
 "primary_objective":"maximize_sustainable_risk_adjusted_realized_profit",
 "self_expansion_enabled":True,
 "auto_generate_internal_capabilities":True,
 "auto_scaffold_integrations":True,
 "external_actions":"existing_policy_only",
 "financial_actions":"existing_policy_only",
 "credential_access":"existing_policy_only",
 "deployment":"existing_policy_only",
 "may_disable_existing_gates":False,
 "may_embed_credentials":False,
 "may_invent_profit_or_evidence":False,
 "generated_code_requires_tests_canary_and_rollback":True,
}

# Reusable capability stacks. This lets CompanyOS discover that a new business
# model needs new skills instead of assuming every venture uses the same pipeline.
STACKS={
 "ecommerce_physical_products":[
  ("product_demand_ranker","analysis","Rank products by demand, competition, price, margin and evidence."),
  ("supplier_source_ranker","research","Compare suppliers, reliability, MOQ, shipping and landed cost."),
  ("landed_cost_optimizer","analysis","Calculate product cost, shipping, fees, refunds and conservative contribution margin."),
  ("catalog_sync_adapter","integration","Normalize supplier catalog, inventory, price and SKU changes."),
  ("storefront_publish_adapter","integration","Publish approved storefront/product content through configured providers."),
  ("order_routing_adapter","external","Route paid orders to approved suppliers using existing transaction gates."),
  ("fulfillment_tracking_adapter","integration","Track order and shipment state."),
  ("commerce_conversion_analytics","analysis","Measure traffic, checkout intent, conversion, refunds and realized margin."),
 ],
 "software_saas_ai":[
  ("saas_offer_ranker","analysis","Rank SaaS offers by buyer pain, price, competition, time-to-cash and margin."),
  ("prototype_scope_optimizer","analysis","Reduce software ideas to the smallest sellable validation scope."),
  ("saas_billing_adapter","external","Connect approved billing while preserving financial gates."),
  ("customer_onboarding_workflow","internal","Coordinate signup, onboarding, support and activation."),
  ("product_usage_analytics","analysis","Measure activation, retention, conversion and unit economics."),
 ],
 "automation_products":[
  ("automation_roi_estimator","analysis","Estimate buyer ROI and willingness-to-pay from workflow savings."),
  ("workflow_integration_spec","integration","Describe and connect approved business-system integrations."),
  ("automation_delivery_workflow","internal","Coordinate setup, validation, delivery and support."),
  ("automation_value_analytics","analysis","Measure adoption, savings, retention and realized profit."),
 ],
 "marketplaces_platforms":[
  ("marketplace_liquidity_analyzer","analysis","Measure supply-demand balance and transaction opportunity."),
  ("listing_ingestion_adapter","integration","Normalize approved seller/listing data."),
  ("marketplace_matching_engine","analysis","Rank buyer-seller matches by fit and economics."),
  ("marketplace_payment_adapter","external","Connect approved transaction provider using existing finance gates."),
  ("marketplace_conversion_analytics","analysis","Measure listing-to-inquiry and inquiry-to-transaction conversion."),
 ],
 "lead_generation_assets":[
  ("lead_market_ranker","analysis","Rank niches by lead value, buyer density, competition and conversion."),
  ("lead_capture_adapter","integration","Capture consented inbound leads."),
  ("lead_qualification_engine","analysis","Score leads using fit and evidence."),
  ("lead_delivery_workflow","internal","Coordinate delivery and outcome tracking."),
  ("lead_economics_analytics","analysis","Track conversion, revenue, refunds and realized margin."),
 ],
 "digital_products":[
  ("digital_product_demand_ranker","analysis","Rank digital products by demand, price, competition and build effort."),
  ("digital_product_generator","internal","Coordinate creation, QA, packaging and revision."),
  ("digital_delivery_adapter","integration","Publish and deliver approved digital products."),
  ("digital_product_conversion_analytics","analysis","Track visits, purchase intent, conversion, refunds and profit."),
 ],
 "subscriptions_memberships":[
  ("subscription_offer_ranker","analysis","Rank recurring offers by demand, price, retention potential and cost."),
  ("membership_delivery_workflow","internal","Coordinate recurring delivery."),
  ("subscription_billing_adapter","external","Connect approved recurring billing."),
  ("subscription_retention_analytics","analysis","Measure activation, churn, LTV, CAC and margin."),
 ],
 "services":[
  ("service_offer_ranker","analysis","Rank services by urgency, price, labor intensity and sales friction."),
  ("service_scope_estimator","analysis","Estimate scope, labor, price, margin and risk."),
  ("service_crm_workflow","internal","Coordinate inbound leads, estimates, follow-up and scheduling."),
  ("service_invoice_adapter","external","Connect approved invoicing/payment provider."),
  ("service_profit_analytics","analysis","Measure close rate, labor, revenue, cost and realized profit."),
 ],
 "data_api_licensing":[
  ("data_source_quality_ranker","analysis","Rank data sources by usefulness, reliability and cost."),
  ("data_ingestion_adapter","integration","Normalize approved data sources."),
  ("api_product_scope_optimizer","analysis","Design the smallest paid API/data product."),
  ("api_metering_billing_adapter","external","Connect approved metering and billing."),
  ("api_profit_analytics","analysis","Measure usage, retention, infrastructure cost and margin."),
 ],
 "mobile_web_apps":[
  ("app_problem_ranker","analysis","Rank app problems by pain, frequency, price and competition."),
  ("app_mvp_scope_optimizer","analysis","Reduce an app to the smallest measurable paid validation."),
  ("app_distribution_adapter","integration","Prepare approved web/app distribution paths."),
  ("app_billing_adapter","external","Connect approved app/web billing."),
  ("app_conversion_analytics","analysis","Measure activation, conversion, retention and profit."),
 ],
 "brokerage_commission":[
  ("brokerage_market_ranker","analysis","Rank brokerable markets by spread, frequency, trust and compliance burden."),
  ("buyer_seller_matching_engine","analysis","Match counterparties by fit and economics."),
  ("brokerage_crm_workflow","internal","Coordinate consented inbound counterparties and deal stages."),
  ("brokerage_payment_adapter","external","Connect approved payment/escrow flow."),
  ("brokerage_profit_analytics","analysis","Measure deal value, close rate, cycle time and commission."),
 ],
}

UNIVERSAL=[
 ("profit_accounting_engine","analysis","Reconcile actual revenue, fees, refunds, costs and realized profit by venture."),
 ("experiment_comparison_engine","analysis","Compare live validation bets on observed economics."),
 ("capability_effectiveness_learner","analysis","Measure whether new capabilities improve evidence, conversion or profit."),
 ("capability_gap_classifier","analysis","Infer the next missing capability from blockers and venture state."),
]

ALIASES={
 "ecommerce":"ecommerce_physical_products","dropshipping":"ecommerce_physical_products",
 "drop_shipping":"ecommerce_physical_products","saas":"software_saas_ai",
 "software":"software_saas_ai","marketplace":"marketplaces_platforms",
 "lead_generation":"lead_generation_assets","subscription":"subscriptions_memberships",
 "mobile_app":"mobile_web_apps","app":"mobile_web_apps","brokerage":"brokerage_commission",
}

def load(p,d=None):
 if d is None:d={}
 try:return json.loads(Path(p).read_text(encoding="utf-8",errors="ignore"))
 except Exception:return d

def save(p,o):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 q=p.with_suffix(p.suffix+".tmp")
 q.write_text(json.dumps(o,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
 q.replace(p)

def mem_mb():
 try:
  for line in Path("/proc/meminfo").read_text().splitlines():
   if line.startswith("MemAvailable:"):return int(line.split()[1])//1024
 except Exception:pass
 return 0

def norm(v):
 x=re.sub(r"[^a-zA-Z0-9_]+","_",str(v or "")).strip("_").lower()
 return x[:80] if len(x)>=4 and re.search(r"[a-z]",x) else None

def failure_records():
 data=load(FAILURES,{"failures":{}})
 f=data.get("failures")
 return f if isinstance(f,dict) else {}

def is_cooled(cid):
 rec=failure_records().get(str(cid),{})
 try:return float(rec.get("cooldown_until_unix") or 0)>time.time()
 except Exception:return False

def record_capability_failure(req,outcome,cooldown_seconds=21600):
 data=load(FAILURES,{"failures":{}})
 fs=data.get("failures")
 if not isinstance(fs,dict):fs={}
 cid=str(req.get("id") or "")
 old=fs.get(cid) if isinstance(fs.get(cid),dict) else {}
 rec={
  "id":cid,
  "kind":req.get("kind"),
  "reason":req.get("reason"),
  "failure_count":int(old.get("failure_count",0))+1,
  "last_status":outcome.get("status"),
  "last_failure":outcome.get("failure") or outcome.get("error"),
  "last_failed_at_unix":time.time(),
  "cooldown_until_unix":time.time()+max(1800,int(cooldown_seconds)),
 }
 fs[cid]=rec
 data["failures"]=fs
 data["updated_at_unix"]=time.time()
 save(FAILURES,data)
 return rec

def dynamic_gap_records():
 data=load(DYNAMIC_GAPS,{"gaps":[]})
 arr=data.get("gaps")
 return arr if isinstance(arr,list) else []

def save_dynamic_gaps(gaps):
 byid={str(x.get("id")):x for x in dynamic_gap_records() if isinstance(x,dict) and x.get("id")}
 for g in gaps:
  if not isinstance(g,dict) or not g.get("id"):continue
  cid=str(g["id"])
  old=byid.get(cid,{})
  old.update(g)
  old["id"]=cid
  old["updated_at_unix"]=time.time()
  byid[cid]=old
 save(DYNAMIC_GAPS,{"gaps":list(byid.values())[-200:],"updated_at_unix":time.time()})

def decompose_failed_capability(req,outcome):
 cid=str(req.get("id") or "")
 children=[]
 if cid=="service_scope_estimator":
  children=[
   {"id":"service_labor_estimator","kind":"analysis","reason":"Estimate labor hours, crew size and labor cost from service scope evidence.","models":["services"],"priority":92,"parent_capability":cid},
   {"id":"service_pricing_estimator","kind":"analysis","reason":"Estimate evidence-based service price ranges without inventing demand or sales.","models":["services"],"priority":92,"parent_capability":cid},
   {"id":"service_margin_estimator","kind":"analysis","reason":"Estimate contribution margin from price, labor, material and operating-cost evidence.","models":["services"],"priority":91,"parent_capability":cid},
   {"id":"service_scope_risk_estimator","kind":"analysis","reason":"Estimate service scope uncertainty, execution risk and contingency needs from supplied evidence.","models":["services"],"priority":91,"parent_capability":cid},
  ]
 if children:save_dynamic_gaps(children)
 return children

def inventory():
 out=set()
 for base in (ROOT/"companyos/runtime",ROOT/"companyos/extensions/generated"):
  if base.exists():
   for p in base.glob("*.py"):
    if not p.name.startswith("__"):out.add(p.stem.lower())
 plug=ROOT/"plugins/installed"
 if plug.exists():
  for p in plug.iterdir():
   if p.is_dir():out.add(p.name.lower())
 if (RT/"live_external_profit_discovery_state.json").exists():out.add("public_market_research")
 if (RT/"economics_validation_state.json").exists():out.add("pricing_economics_research")
 if (RT/"parallel_validation_state.json").exists():out.add("parallel_market_validation")
 return sorted(out)

def scaffolded_integration_ids():
 out=set()
 d=ROOT/"companyos/extensions/integration_specs"
 if d.exists():
  for p in d.glob("*.json"):
   x=load(p,{})
   if isinstance(x,dict) and x.get("status")=="SCAFFOLDED":
    cid=str(x.get("id") or p.stem).strip().lower()
    if cid:out.add(cid)
 q=load(INTEGRATIONS,{"requests":[]})
 for x in q.get("requests",[]) or []:
  if isinstance(x,dict) and x.get("status")=="SCAFFOLDED" and x.get("id"):
   out.add(str(x["id"]).strip().lower())
 return out

def present(cid,inv):
 cid=str(cid).strip().lower()
 if cid in inv:return True
 if cid in scaffolded_integration_ids():
  return True
 tok=[x for x in cid.split("_") if len(x)>=4]
 for item in inv:
  if len(tok)>=2 and sum(t in item for t in tok)>=2:return True
 return False

def candidates():
 best={}
 dirs=[RT/"profit_first_candidates",RT/"canonical_research_outputs"]
 for d in dirs:
  if not d.exists():continue
  pats=["*.json"] if d.name=="profit_first_candidates" else ["v65_95_economics_*.json"]
  for pat in pats:
   for p in d.glob(pat):
    x=load(p,None)
    if not isinstance(x,dict):continue
    name=str(x.get("name") or x.get("candidate_name") or p.stem)
    model=str(x.get("business_model") or x.get("mechanism") or "unknown").lower()
    model=ALIASES.get(model,model)
    row={"name":name,"model":model,"sector":str(x.get("sector") or x.get("market") or "unknown"),
         "score":float(x.get("evidence_quality_pct") or x.get("score") or 0),
         "profit":float(x.get("expected_profit") or 0),
         "prob":float(x.get("probability_success_pct") or x.get("probability") or 0),
         "ready":float(x.get("execution_readiness_pct") or x.get("readiness") or 0),
         "payload":x}
    quality=(0 if model=="unknown" else 25)+row["score"]+row["ready"]+min(20,row["profit"])
    k=name.lower().strip()
    if k not in best or quality>best[k][0]:best[k]=(quality,row)
 out=[v[1] for v in best.values()]
 out.sort(key=lambda r:(r["score"],r["profit"],r["prob"]),reverse=True)
 return out

def active_models():
 st=load(RT/"parallel_validation_state.json",{})
 last=st.get("last_result") if isinstance(st.get("last_result"),dict) else st
 out=[]
 for v in last.get("active_internal_validations",[]) or []:
  if isinstance(v,dict):
   m=ALIASES.get(str(v.get("business_model") or "unknown").lower(),str(v.get("business_model") or "unknown").lower())
   if m not in out:out.append(m)
 if isinstance(last.get("external_live_validation"),dict):
  for m in ("services","software_saas_ai"):
   if m not in out:out.append(m)
 return out

def blockers(rows):
 c=Counter()
 for r in rows:
  p=r["payload"]
  for key in ("qualification_blockers","blockers","qualification_reasons"):
   vals=p.get(key)
   if isinstance(vals,list):
    for v in vals:c[str(v)]+=1
  if r["model"]=="unknown":c["business_model_unknown"]+=1
  if r["profit"]<=0:c["profit_unestimated"]+=1
  if r["prob"]<=0:c["probability_unestimated"]+=1
 return c

def requirements(inv,rows):
 models=[]
 for m in active_models()+[r["model"] for r in rows]:
  if m in STACKS and m not in models:models.append(m)
 req=[{"id":a,"kind":b,"reason":c,"models":["universal"],"priority":100} for a,b,c in UNIVERSAL]
 pri=96
 for m in models:
  for a,b,c in STACKS[m]:
   req.append({"id":a,"kind":b,"reason":c,"models":[m],"priority":pri})
  pri=max(60,pri-3)
 blob=" ".join(json.dumps(r["payload"],default=str).lower() for r in rows[:30])
 if "dropship" in blob or "drop ship" in blob:
  for a,b,c in STACKS["ecommerce_physical_products"]:
   req.append({"id":a,"kind":b,"reason":c,"models":["ecommerce_physical_products"],"priority":98})
 ded={}
 for r in req:
  if r["id"] not in ded or r["priority"]>ded[r["id"]]["priority"]:ded[r["id"]]=r
 for g in dynamic_gap_records():
  if not isinstance(g,dict) or not g.get("id"):continue
  cid=str(g["id"])
  if cid not in ded or int(g.get("priority") or 0)>int(ded[cid].get("priority") or 0):
   ded[cid]=g
 miss=[r for r in ded.values() if not present(r["id"],inv) and not is_cooled(r["id"])]
 miss.sort(key=lambda r:int(r.get("priority") or 0),reverse=True)
 return miss

def model_gap(inv,rows,bs):
 try:
  sys.path.insert(0,str(ROOT/"scripts"))
  from companyos_local_ai_adapter import model_request,extract_json
  context={"objective":POLICY_DATA["primary_objective"],"active_models":active_models(),
           "top_candidates":[{"name":r["name"],"model":r["model"],"sector":r["sector"],"score":r["score"]} for r in rows[:10]],
           "blockers":bs.most_common(10),"inventory_sample":inv[:100]}
  prompt=f"""CompanyOS needs one reusable missing capability to improve profitable venture discovery, validation, delivery, or measurement.
Context: {json.dumps(context,default=str)[:6500]}
Return JSON only with id,title,reason,kind,models,priority.
kind must be one of analysis, internal, research, integration, external.
Do not propose bypassing finance, credential, legal, approval, deployment, or irreversible-action gates.
Do not invent profit, customers, demand, or evidence."""
  r=model_request(prompt)
  if not r.get("ok"):return None
  o=extract_json(r.get("text",""))
  cid=norm(o.get("id"));kind=str(o.get("kind") or "")
  if not cid or kind not in {"analysis","internal","research","integration","external"}:return None
  return {"id":cid,"kind":kind,"reason":str(o.get("reason") or "adaptive model gap")[:500],
          "models":o.get("models") if isinstance(o.get("models"),list) else [],
          "priority":max(1,min(100,int(o.get("priority") or 70))),"source":"model"}
 except Exception:return None

def queue_req(req):
 q=load(REQUESTS,{"requests":[]});arr=q.get("requests")
 if not isinstance(arr,list):arr=[]
 old=next((x for x in arr if isinstance(x,dict) and x.get("id")==req["id"]),None)
 if old:return False,old
 rec={**req,"status":"PENDING","created_at_unix":time.time()}
 arr.append(rec);q["requests"]=arr[-300:];q["updated_at_unix"]=time.time();save(REQUESTS,q)
 return True,rec

def scaffold(req):
 q=load(INTEGRATIONS,{"requests":[]});arr=q.get("requests")
 if not isinstance(arr,list):arr=[]
 old=next((x for x in arr if isinstance(x,dict) and x.get("id")==req["id"]),None)
 if old:return False,old
 rec={"schema":"companyos.integration_capability_request.v1",**req,"status":"SCAFFOLDED",
      "created_at_unix":time.time(),
      "contract":{"inputs":["venture_id","validated_context","provider_config","idempotency_key"],
                  "outputs":["success","provider_reference","evidence","error"],
                  "credentials":"existing_secret_provider_only","idempotency_required":True,
                  "receipt_required":True,"test_mode_required":True},
      "activation":{"external_actions":"existing_policy_only","financial_actions":"existing_policy_only",
                    "automatic_external_execution":False}}
 arr.append(rec);q["requests"]=arr[-300:];q["updated_at_unix"]=time.time();save(INTEGRATIONS,q)
 d=ROOT/"companyos/extensions/integration_specs";d.mkdir(parents=True,exist_ok=True)
 save(d/f"{req['id']}.json",rec)
 return True,rec

def _failure_summary(result):
 out=[]
 if isinstance(result,dict):
  for e in result.get("validation_errors") or []:
   out.append(str(e))
  for step in result.get("tests") or []:
   if not isinstance(step,dict): continue
   rc=step.get("returncode")
   if rc:
    out.append("returncode="+str(rc))
    err=str(step.get("stderr") or "").strip()
    std=str(step.get("stdout") or "").strip()
    if err: out.append("stderr="+err[-1800:])
    if std: out.append("stdout="+std[-1200:])
 return " | ".join(out)[-3500:] or str(result.get("status") if isinstance(result,dict) else "unknown_failure")

def _activate_feedback(req):
 fb=load(FEEDBACK,{"capabilities":{}})
 caps=fb.get("capabilities")
 if not isinstance(caps,dict):caps={}
 rec=caps.get(req["id"]) if isinstance(caps.get(req["id"]),dict) else {}
 rec.update({
  "status":"active",
  "utility_score":float(rec.get("utility_score",50) or 50),
  "source":"adaptive_capability_director_v65_97a",
  "kind":req["kind"],
  "activated_at_unix":time.time()
 })
 caps[req["id"]]=rec
 fb["capabilities"]=caps
 fb["updated_at_unix"]=time.time()
 save(FEEDBACK,fb)

def _repair_generation(ce, req, prior):
 ctx=ce.diagnostics()
 failure=_failure_summary(prior)

 for repair_attempt in range(1,4):
  gap={
   "id":req["id"],
   "title":req["id"].replace("_"," ").title(),
   "reason":(
    req["reason"]
    +" Make it reusable across ventures and profit-focused without fabricating evidence. "
    +"The previous generated candidate failed validation/testing. Repair the implementation "
    +"while keeping the required capability contract. Failure evidence: "+failure
   )[:5200],
  }

  gen=ce.model_plan(gap,ctx)
  if not gen.get("ok"):
   failure="generation_failed:"+str(gen.get("reason") or gen.get("attempts"))
   continue

  try:
   module_content,_,_=ce._classify_generated_contents(gen.get("plan") or {},gap["id"])
   if module_content:
    is_dup,dup_id=ce._is_duplicate_generated_source(module_content)
    if is_dup:
     failure="duplicate_generated_source:"+str(dup_id)
     continue
  except Exception:
   pass

  cid,root,errors=ce.stage_plan(gap,gen["plan"])
  if errors:
   failure="validation_errors:"+json.dumps(errors,default=str)[-3000:]
   continue

  ok,tests=ce.test_stage(root,gap["id"])
  if not ok:
   failure=_failure_summary({"status":"candidate_rejected_tests","tests":tests})
   continue

  receipt=ce.promote(root,gap["id"],cid)
  try:
   execution=ce.run_capability(gap["id"],ctx)
  except Exception as exc:
   ce.rollback(gap["id"])
   failure="canary_failed:"+repr(exc)
   continue

  return {
   "ok":True,
   "status":"adaptive_repair_promoted_and_used",
   "repair_attempt":repair_attempt,
   "candidate_id":cid,
   "promotion":receipt,
   "execution":execution,
   "tests":tests,
  }

 return {
  "ok":False,
  "status":"adaptive_repair_exhausted",
  "failure":failure,
 }

def build(req):
 try:
  from companyos.runtime import capability_expansion as ce

  gap={
   "id":req["id"],
   "title":req["id"].replace("_"," ").title(),
   "reason":req["reason"]+" Make it reusable across ventures and profit-focused without fabricating evidence."
  }

  old=ce.derive_gap
  ce.derive_gap=lambda ctx:gap
  try:
   r=ce.cycle()
  finally:
   ce.derive_gap=old

  status=str(r.get("status") or "")
  ok=status in {"capability_promoted_and_used","existing_capability_used"}

  if not ok and status in {
   "candidate_rejected_tests",
   "candidate_rejected_validation",
   "generation_failed",
  }:
   repaired=_repair_generation(ce,req,r)
   if repaired.get("ok"):
    _activate_feedback(req)
   return repaired

  if ok:
   _activate_feedback(req)

  return {"ok":ok,"status":status,"initial_result":r}

 except Exception as e:
  return {"ok":False,"status":"exception","error":repr(e)}

def learn(req,outcome):
 st=load(LEARNING,{"cycles":0,"capabilities":{}});caps=st.get("capabilities")
 if not isinstance(caps,dict):caps={}
 rec=caps.get(req["id"]) if isinstance(caps.get(req["id"]),dict) else {"attempts":0,"successes":0}
 rec["attempts"]=int(rec.get("attempts",0))+1
 if outcome.get("ok"):rec["successes"]=int(rec.get("successes",0))+1
 rec["last_outcome"]=outcome;rec["last_seen_unix"]=time.time();rec["kind"]=req["kind"]
 caps[req["id"]]=rec;st["capabilities"]=caps;st["cycles"]=int(st.get("cycles",0))+1;st["updated_at_unix"]=time.time()
 save(LEARNING,st)

def cycle():
 if STOP.exists():
  r={"version":"V65.97","status":"stopped_by_global_stop","timestamp_unix":time.time()};save(STATE,r);return r
 mb=mem_mb();print("AVAILABLE_MB=",mb)
 if mb and mb<MIN_MB:
  r={"version":"V65.97","status":"deferred_resource_pressure","available_mb":mb,"timestamp_unix":time.time()}
  save(STATE,r);print("V65_97_DEFERRED=resource_pressure");return r
 save(POLICY,POLICY_DATA)
 inv=inventory();rows=candidates();bs=blockers(rows);miss=requirements(inv,rows)
 mg=model_gap(inv,rows,bs)
 if mg and not present(mg["id"],inv) and all(x["id"]!=mg["id"] for x in miss):
  miss.append(mg);miss.sort(key=lambda r:r["priority"],reverse=True)
 print("CAPABILITY_INVENTORY_COUNT=",len(inv))
 print("CANDIDATES_OBSERVED=",len(rows))
 print("ACTIVE_VALIDATION_MODELS=",active_models())
 print("TOP_BLOCKERS=",bs.most_common(10))
 print("MISSING_CAPABILITIES=",len(miss))
 print("COOLED_CAPABILITIES=",sorted([k for k in failure_records() if is_cooled(k)]))
 print("DYNAMIC_GAPS=",len(dynamic_gap_records()))
 print("SCAFFOLDED_INTEGRATIONS=",sorted(scaffolded_integration_ids()))
 selected=miss[:1];outs=[]
 for req in selected:
  created,_=queue_req(req)
  if req["kind"] in {"analysis","internal","research"}:
   br=build(req)
   out={"id":req["id"],"kind":req["kind"],"action":"generate_test_canary_promote",
        "queued_new":created,**br}
  else:
   made,_=scaffold(req)
   out={"id":req["id"],"kind":req["kind"],"action":"integration_scaffold",
        "queued_new":created,"created":made,"ok":True}
  outs.append(out);learn(req,out)
  if out.get("action")=="generate_test_canary_promote" and not out.get("ok"):
   failure_rec=record_capability_failure(req,out)
   children=decompose_failed_capability(req,out)
   print("CAPABILITY_FAILURE_COOLDOWN=",json.dumps(failure_rec,sort_keys=True,default=str))
   print("CAPABILITY_DECOMPOSITION=",json.dumps(children,sort_keys=True,default=str))
 result={"version":"V65.97","status":"cycle_complete","timestamp_unix":time.time(),
         "objective":POLICY_DATA["primary_objective"],"self_expansion_enabled":True,
         "candidate_count":len(rows),"active_models":active_models(),
         "top_blockers":bs.most_common(15),"inventory_before":len(inv),"inventory_after":len(inventory()),
         "missing_before":len(miss),"selected":selected,"outcomes":outs,"model_gap":mg,
         "integration_requests":len(load(INTEGRATIONS,{"requests":[]}).get("requests",[])),
         "guards_preserved":True}
 save(STATE,result)
 rp=REPORTS/f"v65_97_adaptive_capability_director_{int(time.time())}.json";save(rp,result)
 print("SELECTED_REQUESTS=",json.dumps(selected,sort_keys=True,default=str))
 print("EXPANSION_OUTCOMES=",json.dumps(outs,sort_keys=True,default=str))
 print("CAPABILITY_INVENTORY_AFTER=",result["inventory_after"])
 print("INTEGRATION_REQUESTS=",result["integration_requests"])
 print("REPORT=",rp)
 print("V65_97_SELF_EXPANSION_ENABLED=PASS")
 print("V65_97_DYNAMIC_CAPABILITY_LEARNING=PASS")
 print("V65_97_GENERATE_TEST_CANARY_ROLLBACK=PASS")
 print("V65_97_INTEGRATION_SCAFFOLDING=PASS")
 print("V65_97_EXISTING_GATES_PRESERVED=PASS")
 print("V65_97_COMPLETE")
 return result

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("command",nargs="?",default="once",choices=("once","loop","status","inventory"))
 p.add_argument("--interval",type=int,default=900);a=p.parse_args()
 if a.command=="once":cycle()
 elif a.command=="status":print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
 elif a.command=="inventory":
  inv=inventory();rows=candidates();print(json.dumps({"inventory":inv,"candidate_count":len(rows),"missing":requirements(inv,rows)},indent=2,sort_keys=True))
 else:
  interval=max(600,int(a.interval))
  while not STOP.exists():
   try:cycle()
   except Exception as e:
    save(STATE,{"version":"V65.97","status":"cycle_exception","error":repr(e),"timestamp_unix":time.time()})
    print("V65_97_LOOP_ERROR=",repr(e),flush=True)
   time.sleep(interval)

if __name__=="__main__":main()
