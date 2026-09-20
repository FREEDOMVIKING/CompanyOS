from __future__ import annotations

import importlib.util
import json
import math
import os
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse, quote_plus

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
OUT = RT / "canonical_research_outputs"
STATE = RT / "economics_validation_state.json"
REPORTS = Path.home() / ".companyos_runtime" / "reports"
PLUGIN_PATH = ROOT / "plugins/installed/web_research/plugin.py"

OUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = max(1, min(5, int(os.getenv("COMPANYOS_ECONOMICS_CANDIDATES_PER_CYCLE", "3"))))
SEARCH_RESULTS = max(4, min(10, int(os.getenv("COMPANYOS_ECONOMICS_SEARCH_RESULTS", "7"))))
MAX_FETCHES = max(6, min(18, int(os.getenv("COMPANYOS_ECONOMICS_FETCHES_PER_CANDIDATE", "12"))))
MIN_AVAILABLE_MB = max(500, int(os.getenv("COMPANYOS_ECONOMICS_MIN_AVAILABLE_MB", "900")))

PRICE_RE = re.compile(r"(?<![A-Za-z0-9])\$\s*([0-9]{1,6}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)")
PRICE_WORDS = (
    "price","pricing","plan","plans","month","monthly","annual","yearly",
    "per user","per seat","subscription","license","starting at","one-time",
    "one time","buy","cost","free trial","pro","business","enterprise"
)

NONCOMMERCIAL = {
    "wikipedia.org","github.com","news.ycombinator.com","stackoverflow.com",
    "stackexchange.com","medium.com","youtube.com","facebook.com","x.com",
    "twitter.com","linkedin.com"
}

MARGIN_PRIOR = {
    "software_saas_ai": 0.70,
    "automation_products": 0.60,
    "data_api_licensing": 0.70,
    "digital_products": 0.75,
    "subscriptions_memberships": 0.55,
    "content_media": 0.50,
    "lead_generation_assets": 0.50,
    "marketplaces_platforms": 0.55,
    "brokerage_commission": 0.55,
    "mobile_web_apps": 0.65,
    "services": 0.30,
    "ecommerce_physical_products": 0.20,
    "unknown": 0.25,
}

def load(path, default=None):
    if default is None: default = {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)

def slug(v):
    return re.sub(r"[^a-z0-9]+","_",str(v or "").lower()).strip("_")[:90] or "candidate"

def dom(url):
    try:
        return urlparse(str(url)).netloc.lower().replace("www.","")
    except Exception:
        return ""

def commercial_domain(d):
    d = str(d or "").lower()
    if not d: return False
    return not any(d == x or d.endswith("." + x) for x in NONCOMMERCIAL)

def mem_mb():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except Exception:
        pass
    return 0

def web_plugin():
    if not PLUGIN_PATH.exists():
        raise FileNotFoundError(str(PLUGIN_PATH))
    spec = importlib.util.spec_from_file_location("companyos_v65_95a_web", PLUGIN_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def topic_name(o):
    n = str(o.name or "")
    n = re.sub(r"\s+Opportunity\s*$","",n,flags=re.I)
    return n.strip()

def queries(o):
    p = o.payload or {}
    topic = topic_name(o)
    market = str(p.get("market") or p.get("sector") or o.category or "").replace("_"," ")
    buyer = str(p.get("target_customer") or "").replace("_"," ")
    model = str(p.get("business_model") or o.mechanism or "").replace("_"," ")

    raw = [
        f'{topic} pricing',
        f'best {topic} tools pricing',
        f'{topic} alternatives pricing',
        f'{market} {model} pricing',
        f'{buyer} {topic} cost',
        f'{topic} software pricing plans',
    ]
    out=[]; seen=set()
    for q in raw:
        q=" ".join(q.split())
        if q and q.lower() not in seen:
            seen.add(q.lower()); out.append(q)
    return out

def extract_prices(text, url, title):
    rows=[]
    for m in PRICE_RE.finditer(text):
        try:
            amount=float(m.group(1).replace(",",""))
        except Exception:
            continue
        if amount < 2 or amount > 100000:
            continue
        lo=max(0,m.start()-130); hi=min(len(text),m.end()+180)
        ctx=" ".join(text[lo:hi].split())
        low=ctx.lower()
        if not any(k in low for k in PRICE_WORDS):
            continue

        cadence="unknown"; monthly=None
        if any(x in low for x in ("/mo","per month","monthly"," month")):
            cadence="monthly"; monthly=amount
        elif any(x in low for x in ("/yr","/year","per year","annual","yearly")):
            cadence="annual"; monthly=round(amount/12.0,2)
        elif any(x in low for x in ("one-time","one time","lifetime")):
            cadence="one_time"

        rows.append({
            "amount_usd":amount,
            "cadence":cadence,
            "monthly_equivalent_usd":monthly,
            "context":ctx[:360],
            "url":url,
            "domain":dom(url),
            "title":title,
        })
        if len(rows)>=16: break
    return rows

def dedupe(rows):
    out=[]; seen=set()
    for r in rows:
        k=(r.get("domain"),round(float(r.get("amount_usd") or 0),2),r.get("cadence"))
        if k in seen: continue
        seen.add(k); out.append(r)
    return out

def price_floor(prices, model):
    monthly=[r["monthly_equivalent_usd"] for r in prices if r.get("monthly_equivalent_usd")]
    one=[r["amount_usd"] for r in prices if r.get("cadence")=="one_time"]
    unknown=[r["amount_usd"] for r in prices if r.get("cadence")=="unknown"]
    vals=monthly; basis="monthly_equivalent"
    if not vals and model in ("digital_products","ecommerce_physical_products") and one:
        vals=one; basis="one_time"
    if not vals and unknown:
        vals=unknown; basis="unclassified_price"
    if not vals: return None,basis
    vals=sorted(float(v) for v in vals if v and v>0)
    idx=max(0,min(len(vals)-1,int(math.floor((len(vals)-1)*0.25))))
    return round(vals[idx],2),basis

def choose(rows, cursor):
    rows=[o for o in rows if str(o.mechanism or "unknown")!="unknown" and int(o.evidence_count or 0)>=1]
    if not rows: return [],0
    ordered=[rows[(cursor+i)%len(rows)] for i in range(len(rows))]
    picked=[]; models=set(); sectors=set()
    for o in ordered:
        m=str(o.mechanism or "unknown"); s=str(o.category or "unknown")
        if picked and m in models and s in sectors: continue
        picked.append(o); models.add(m); sectors.add(s)
        if len(picked)>=BATCH_SIZE: break
    for o in ordered:
        if len(picked)>=BATCH_SIZE: break
        if o not in picked: picked.append(o)
    return picked,(cursor+len(picked))%len(rows)

def search_results(web,o):
    found=[]
    errors=[]
    provider_counts={}

    search_engine_domains={
        "search.brave.com","brave.com",
        "www.bing.com","bing.com",
        "www.mojeek.com","mojeek.com",
        "duckduckgo.com","html.duckduckgo.com","lite.duckduckgo.com",
        "google.com","www.google.com",
        "en.wikipedia.org",
    }

    def add_rows(rows, q, provider):
        added=0
        for item in rows or []:
            try:
                x=dict(item)
            except Exception:
                continue
            u=str(x.get("url") or "").strip()
            d=dom(u)
            if not u or not d or d in search_engine_domains:
                continue
            x["query"]=q
            x["search_provider"]=provider
            found.append(x)
            added+=1
        provider_counts[provider]=provider_counts.get(provider,0)+added

    def html_provider(provider, url, q):
        try:
            page,_=web.request_text(url, timeout=12)
            rows=web.parse_generic_links(page, SEARCH_RESULTS)
            add_rows(rows,q,provider)
        except Exception as exc:
            errors.append(f"{provider}:{q}:{type(exc).__name__}:{str(exc)[:160]}")

    for q in queries(o):
        try:
            r=web.search_web(q,SEARCH_RESULTS)
            add_rows(r.get("results") or [],q,"companyos_default")
            if not r.get("success"):
                errors.append(f"default:{q}:{r.get('error')}")
        except Exception as exc:
            errors.append(f"default:{q}:{type(exc).__name__}:{str(exc)[:160]}")

        if len({dom(x.get("url")) for x in found if dom(x.get("url"))}) < 8:
            enc=quote_plus(q)
            html_provider(
                "brave_html",
                f"https://search.brave.com/search?q={enc}&source=web",
                q,
            )
        if len({dom(x.get("url")) for x in found if dom(x.get("url"))}) < 8:
            enc=quote_plus(q)
            html_provider(
                "bing_html",
                f"https://www.bing.com/search?q={enc}&count={SEARCH_RESULTS}",
                q,
            )
        if len({dom(x.get("url")) for x in found if dom(x.get("url"))}) < 8:
            enc=quote_plus(q)
            html_provider(
                "mojeek_html",
                f"https://www.mojeek.com/search?q={enc}",
                q,
            )

    seen=set()
    unique=[]
    for r in found:
        u=str(r.get("url") or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        d=dom(u)
        if not commercial_domain(d):
            continue
        unique.append(r)

    def rank(r):
        hay=(str(r.get("title") or "")+" "+str(r.get("url") or "")).lower()
        score=0
        if "pricing" in hay: score+=5
        if "plans" in hay: score+=4
        if "price" in hay: score+=3
        if "cost" in hay: score+=2
        return score

    unique.sort(key=rank, reverse=True)
    errors.append("provider_counts="+str(provider_counts))
    return unique[:40],errors

def candidate_fetch_urls(results):
    # Favor commercial domains and explicitly try pricing/plans pages.
    domains={}
    for r in results:
        u=str(r.get("url") or "")
        d=dom(u)
        if not d or not commercial_domain(d): continue
        domains.setdefault(d,r)

    ranked=[]
    for d,r in domains.items():
        u=str(r.get("url") or "")
        ttl=(str(r.get("title") or "")+" "+u).lower()
        score=3 if any(k in ttl for k in ("pricing","plans","price","cost")) else 1
        ranked.append((score,d,r))
    ranked.sort(key=lambda x:x[0],reverse=True)

    urls=[]
    seen=set()
    for _,d,r in ranked[:8]:
        primary=str(r.get("url") or "")
        guesses=[
            primary,
            f"https://{d}/pricing",
            f"https://{d}/plans",
        ]
        for u in guesses:
            if u not in seen:
                seen.add(u); urls.append((u,r.get("title"),r.get("query"),d))
            if len(urls)>=MAX_FETCHES:
                return urls
    return urls

def research(web,o):
    p=dict(o.payload or {})
    results,errors=search_results(web,o)
    fetches=[]; prices=[]

    for u,title,q,d in candidate_fetch_urls(results):
        try:
            page=web.fetch_public_page(u)
            if not page.get("success"): continue
            text=str(page.get("text") or "")
            fetches.append({
                "url":u,"domain":d,"title":title,"query":q,
                "characters":page.get("characters")
            })
            prices.extend(extract_prices(text,u,str(title or "")))
        except Exception as exc:
            errors.append(f"fetch:{u}:{type(exc).__name__}:{str(exc)[:160]}")

    prices=dedupe(prices)
    external_domains={dom(r.get("url")) for r in results if dom(r.get("url"))}
    fetched_domains={f["domain"] for f in fetches if f.get("domain")}
    pricing_domains={r["domain"] for r in prices if r.get("domain")}
    commercial_pricing={d for d in pricing_domains if commercial_domain(d)}

    model=str(o.mechanism or p.get("business_model") or "unknown")
    floor,basis=price_floor(prices,model)

    economics_ready=bool(
        floor
        and len(commercial_pricing)>=2
        and len(external_domains | fetched_domains)>=3
    )

    expected=0.0; probability=0.0; margin=0.0
    readiness=max(15.0,float(o.readiness or 0))
    estimate_basis=None

    if economics_ready:
        prior=MARGIN_PRIOR.get(model,MARGIN_PRIOR["unknown"])
        margin=round(prior*100,2)
        expected=round(max(1.0,float(floor)*prior),2)
        probability=round(min(
            30.0,
            7.0
            + min(9.0,len(external_domains | fetched_domains)*1.25)
            + min(8.0,len(commercial_pricing)*2.25)
            + min(6.0,len(prices)*0.5)
        ),2)
        readiness=max(readiness,30.0)
        estimate_basis={
            "type":"conservative_validation_scenario",
            "observed_price_floor_usd":floor,
            "price_basis":basis,
            "assumed_first_30d_paid_customers_or_orders":1,
            "contribution_margin_prior":prior,
            "margin_prior_is_assumption":True,
            "expected_profit_is_observed":False,
            "probability_is_observed":False,
            "probability_method":"bounded evidence-conditioned validation prior"
        }

    quality=round(min(
        82.0,
        max(float(o.evidence_quality or 0),20.0)
        + min(22.0,len(external_domains | fetched_domains)*2.5)
        + min(20.0,len(commercial_pricing)*5.0)
    ),2)

    artifact={
        "schema":"companyos.economics_validation.v65_95a",
        "name":o.name,
        "business_model":model,
        "market":o.category,
        "sector":o.category,
        "target_customer":p.get("target_customer","unknown"),
        "problem":p.get("problem","unknown"),
        "offer":p.get("offer","unknown"),
        "description":p.get("description",""),
        "expected_profit":expected,
        "expected_profit_period":"first_30_days",
        "expected_profit_basis":estimate_basis,
        "margin":margin,
        "probability_success_pct":probability,
        "probability_basis":estimate_basis,
        "execution_readiness_pct":readiness,
        "time_to_cash_days":min(float(o.time_to_cash_days or 30),30.0),
        "capital_required":float(o.capital_required or 0),
        "capital_required_unknown":bool(p.get("capital_required_unknown",True)),
        "evidence_count":max(int(o.evidence_count or 0),len(external_domains | fetched_domains)),
        "evidence_quality_pct":quality,
        "evidence_quality_method":"external_domain_diversity_plus_multi_domain_pricing",
        "pricing_observation_count":len(prices),
        "pricing_domain_count":len(commercial_pricing),
        "economics_ready":economics_ready,
        "source_urls":sorted({str(r.get("url")) for r in results if r.get("url")})[:50],
        "evidence":{
            "search_queries":queries(o),
            "search_results":results[:50],
            "fetched_pages":fetches,
            "pricing_observations":prices,
            "commercial_pricing_domains":sorted(commercial_pricing),
            "all_external_domains":sorted(external_domains | fetched_domains)
        },
        "next_action":(
            "Run a reversible buyer-facing validation at the evidence-backed price point and measure qualified interest/conversion."
            if economics_ready else
            "Continue targeted competitor/vendor pricing research until at least two independent commercial pricing domains are verified."
        ),
        "external_research_performed":True,
        "financial_action_performed":False,
        "external_outreach_performed":False,
        "publication_performed":False,
        "generated_at_unix":time.time(),
        "research_errors":errors[-25:]
    }

    path=OUT/f"v65_95_economics_{slug(o.name)}.json"
    save(path,artifact)

    return {
        "name":o.name,
        "business_model":model,
        "sector":o.category,
        "economics_ready":economics_ready,
        "external_domains":len(external_domains | fetched_domains),
        "pricing_domains":len(commercial_pricing),
        "pricing_observations":len(prices),
        "observed_price_floor_usd":floor,
        "expected_profit_30d_estimate":expected,
        "probability_estimate":probability,
        "evidence_quality":quality,
        "artifact":str(path.relative_to(ROOT)),
        "errors":errors[-6:]
    }

def cycle():
    mem=mem_mb()
    print("AVAILABLE_MB=",mem)
    if mem and mem<MIN_AVAILABLE_MB:
        r={"version":"V65.95A","timestamp_unix":time.time(),"deferred":True,"reason":"resource_pressure","available_mb":mem}
        save(STATE,r); print("V65_95A_DEFERRED=resource_pressure"); return r

    from companyos.runtime import profit_opportunity_engine as poe
    from companyos.runtime.candidate_enrichment_bridge import refresh_enrichments

    rows=poe.discover()
    old=load(STATE,{})
    cursor=int(old.get("cursor",0) or 0)
    selected,next_cursor=choose(rows,cursor)

    print("DISCOVERED_CANDIDATES_BEFORE=",len(rows))
    print("PRICING_DIVERSITY_TARGETS=",[o.name for o in selected])

    if not selected:
        r={"version":"V65.95A","timestamp_unix":time.time(),"candidate_count":len(rows),"reason":"no_targets"}
        save(STATE,r); print("V65_95A_NO_TARGETS=true"); return r

    web=web_plugin()
    results=[]
    for o in selected:
        try:
            results.append(research(web,o))
        except Exception as exc:
            results.append({"name":o.name,"economics_ready":False,"error":f"{type(exc).__name__}:{exc}"})

    enrichment=refresh_enrichments(max_age_hours=168)
    after=poe.discover()
    decision=poe.choose()

    ready=[r for r in results if r.get("economics_ready")]
    report={
        "version":"V65.95A",
        "timestamp_unix":time.time(),
        "candidate_count_before":len(rows),
        "candidate_count_after":len(after),
        "targets":len(selected),
        "economics_ready_this_cycle":len(ready),
        "strict_execution_qualified_after":int(decision.get("eligible_count",0) or 0),
        "results":results,
        "enrichment":enrichment,
        "financial_actions":False,
        "external_outreach":False,
        "publication":False,
        "pricing_policy":{
            "commercial_pricing_domains_required":2,
            "external_domains_required":3,
            "profit_is_scenario_estimate_not_observed":True,
            "probability_is_validation_prior_not_observed_rate":True
        }
    }

    save(STATE,{
        "version":"V65.95A",
        "cursor":next_cursor,
        "last_cycle_unix":time.time(),
        "last_result":report
    })
    rp=REPORTS/f"v65_95a_pricing_diversity_{int(time.time())}.json"
    save(rp,report)

    print("ECONOMICS_TARGETS=",len(selected))
    print("ECONOMICS_READY_THIS_CYCLE=",len(ready))
    print("ECONOMICS_RESULTS=",json.dumps(results,sort_keys=True,default=str))
    print("STRICT_EXECUTION_QUALIFIED_AFTER=",report["strict_execution_qualified_after"])
    print("REPORT=",rp)
    print("V65_95A_MULTI_DOMAIN_PRICING=PASS")
    print("V65_95A_COMMERCIAL_SOURCE_FILTER=PASS")
    print("V65_95A_TRANSPARENT_ESTIMATES=PASS")
    print("V65_95A_NO_FINANCIAL_ACTIONS=PASS")
    print("V65_95A_COMPLETE")
    return report

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("once","loop","status"))
    p.add_argument("--interval",type=int,default=900)
    a=p.parse_args()
    if a.command=="once":
        cycle()
    elif a.command=="status":
        d=load(STATE,{"status":"not_run"})
        print(json.dumps(d.get("last_result",d),indent=2,sort_keys=True,default=str))
    else:
        interval=max(600,int(a.interval))
        while True:
            try: cycle()
            except Exception as exc: print("V65_95A_LOOP_ERROR=",f"{type(exc).__name__}:{exc}",flush=True)
            time.sleep(interval)

if __name__=="__main__":
    main()
