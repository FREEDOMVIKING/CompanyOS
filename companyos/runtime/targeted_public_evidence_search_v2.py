from __future__ import annotations
import html
import json
import re
import time
import urllib.parse
from pathlib import Path
from typing import Callable

from companyos.runtime import targeted_public_evidence_research as base

RT=Path.home()/".companyos_runtime"
RESEARCH_DIR=RT/"canonical_research_outputs"
STATE=RT/"targeted_public_evidence_search_v2_state.json"

BLOCKED={
    "duckduckgo.com","html.duckduckgo.com","lite.duckduckgo.com",
    "bing.com","www.bing.com","search.brave.com","google.com","www.google.com",
    "yahoo.com","www.yahoo.com","facebook.com","instagram.com","youtube.com","tiktok.com",
}

def _domain(url):
    try:
        d=urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return ""
    return d[4:] if d.startswith("www.") else d

def _clean(s):
    s=re.sub(r"<[^>]+>"," ",str(s or ""))
    return re.sub(r"\s+"," ",html.unescape(s)).strip()

def _usable(url):
    return str(url).startswith(("http://","https://")) and _domain(url) not in BLOCKED and bool(_domain(url))

def _dedupe(rows):
    out=[]; seen=set()
    for r in rows:
        url=str(r.get("url") or "")
        if not _usable(url) or url in seen:
            continue
        seen.add(url)
        out.append({
            "url":url,
            "title":_clean(r.get("title"))[:500],
            "domain":_domain(url),
            "provider":r.get("provider"),
        })
        if len(out)>=8:
            break
    return out

def _unwrap_ddg(href):
    href=html.unescape(str(href or ""))
    if href.startswith("//"):
        href="https:"+href
    p=urllib.parse.urlparse(href)
    if "duckduckgo.com" in p.netloc:
        q=urllib.parse.parse_qs(p.query)
        if q.get("uddg"):
            return urllib.parse.unquote(q["uddg"][0])
    return href

def search_ddg_html(query):
    url="https://html.duckduckgo.com/html/?"+urllib.parse.urlencode({"q":query})
    body,_=base._request(url,750000)
    pat=re.compile(r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',re.I|re.S)
    return _dedupe([
        {"url":_unwrap_ddg(h),"title":t,"provider":"ddg_html"}
        for h,t in pat.findall(body)
    ])

def search_ddg_lite(query):
    url="https://lite.duckduckgo.com/lite/?"+urllib.parse.urlencode({"q":query})
    body,_=base._request(url,750000)
    rows=[]
    for pat in (
        re.compile(r'<a[^>]+rel=["\']nofollow["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',re.I|re.S),
        re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']nofollow["\'][^>]*>(.*?)</a>',re.I|re.S),
    ):
        rows += [{"url":_unwrap_ddg(h),"title":t,"provider":"ddg_lite"} for h,t in pat.findall(body)]
    return _dedupe(rows)

def search_bing(query):
    url="https://www.bing.com/search?"+urllib.parse.urlencode({"q":query,"count":8,"setlang":"en-us"})
    body,_=base._request(url,900000)
    rows=[]
    for block in re.findall(r'<li[^>]+class=["\'][^"\']*b_algo[^"\']*["\'][^>]*>(.*?)</li>',body,re.I|re.S):
        m=re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',block,re.I|re.S)
        if m:
            rows.append({"url":html.unescape(m.group(1)),"title":m.group(2),"provider":"bing"})
    return _dedupe(rows)

def search_brave(query):
    url="https://search.brave.com/search?"+urllib.parse.urlencode({"q":query,"source":"web"})
    body,_=base._request(url,900000)
    rows=[]
    for h,t in re.findall(r'<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>',body,re.I|re.S):
        if len(_clean(t))>=4:
            rows.append({"url":html.unescape(h),"title":t,"provider":"brave"})
    return _dedupe(rows)

PROVIDERS:tuple[tuple[str,Callable],...]=(
    ("ddg_html",search_ddg_html),
    ("ddg_lite",search_ddg_lite),
    ("bing",search_bing),
    ("brave",search_brave),
)

def search_all(query):
    merged=[]; seen=set(); diag=[]
    for name,fn in PROVIDERS:
        t=time.time()
        try:
            rows=fn(query); err=None
        except Exception as exc:
            rows=[]; err=f"{type(exc).__name__}:{str(exc)[:160]}"
        diag.append({
            "provider":name,"query":query,"results":len(rows),
            "error":err,"elapsed":round(time.time()-t,3),
        })
        for r in rows:
            if r["url"] not in seen:
                seen.add(r["url"]); merged.append(r)
    return merged,diag

def expanded_queries(candidate,requirement):
    q=list(base.build_queries(candidate,requirement))
    market=base.compact_phrase(candidate.get("market") or candidate.get("sector") or "business")
    buyer=base.compact_phrase(candidate.get("target_customer") or "business customer")
    offer=base.compact_phrase(candidate.get("offer") or candidate.get("problem") or market)
    if requirement=="pricing":
        extra=[
            f"{market} {offer} pricing",
            f"{buyer} estimating software price",
            f"{market} estimating software cost",
            f"{market} contractor software pricing plans",
        ]
    else:
        extra=[
            f"{market} {offer} customer case study",
            f"{buyer} estimating software customers",
            f"{market} contractor software adoption",
            f"{market} estimating software testimonials",
        ]
    out=[]; seen=set()
    for x in q+extra:
        x=re.sub(r"\s+"," ",x).strip()
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out[:8]

def research_candidate(candidate_name,requirements):
    path,candidate=base.candidate_payload(candidate_name)
    if not path or not candidate:
        raise RuntimeError("candidate_not_found")
    anchors=base.candidate_terms(candidate,candidate_name)
    if len(anchors)<2:
        raise RuntimeError("candidate_anchor_set_too_small")

    started=time.time()
    source_rows=[]
    query_diag=[]
    page_diag=[]
    errors=[]
    seen_urls=set()

    for requirement in requirements:
        accepted=0
        checked=0
        for query in expanded_queries(candidate,requirement):
            if accepted>=5 or checked>=16:
                break
            results,diag=search_all(query)
            for d in diag:
                d["requirement"]=requirement
            query_diag.extend(diag)

            for result in results:
                if accepted>=5 or checked>=16:
                    break
                url=result["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                checked+=1

                row={
                    "requirement":requirement,
                    "provider":result.get("provider"),
                    "url":url,
                    "domain":result.get("domain"),
                    "accepted":False,
                    "reason":None,
                }
                try:
                    title,text=base.fetch_page(url)
                except Exception as exc:
                    row["reason"]=f"fetch_error:{type(exc).__name__}:{str(exc)[:120]}"
                    page_diag.append(row); errors.append(row["reason"]); continue

                if not text:
                    row["reason"]="empty_page"
                    page_diag.append(row); continue

                ok,hits=base.page_supports_requirement(
                    title or result.get("title",""),text,requirement,anchors
                )
                if not ok:
                    row["reason"]="candidate_or_requirement_mismatch"
                    row["anchor_hits"]=hits
                    page_diag.append(row); continue

                excerpt=base.evidence_excerpt(text,requirement,anchors)
                if not excerpt:
                    row["reason"]="empty_excerpt"
                    page_diag.append(row); continue

                source_rows.append({
                    "source":result.get("domain") or "public_web",
                    "publisher":result.get("domain") or "public_web",
                    "url":url,
                    "title":(title or result.get("title") or "")[:500],
                    "summary":excerpt,
                    "observed_at":time.time(),
                })
                row["accepted"]=True
                row["reason"]="accepted"
                row["anchor_hits"]=hits
                page_diag.append(row)
                accepted+=1

    provider_summary={}
    for d in query_diag:
        s=provider_summary.setdefault(d["provider"],{"queries":0,"results":0,"errors":0})
        s["queries"]+=1
        s["results"]+=int(d.get("results") or 0)
        if d.get("error"): s["errors"]+=1

    rejection_summary={}
    for d in page_diag:
        r=str(d.get("reason") or "unknown")
        rejection_summary[r]=rejection_summary.get(r,0)+1

    artifact={
        "schema":"companyos.targeted_public_evidence.v69_22",
        "candidate_name":candidate_name,
        "candidate_source":str(path),
        "candidate_anchors":anchors,
        "requirements_requested":requirements,
        "source_rows":source_rows,
        "source_row_count":len(source_rows),
        "provider_summary":provider_summary,
        "query_diagnostics":query_diag,
        "page_diagnostics":page_diag,
        "rejection_summary":rejection_summary,
        "errors":errors[-30:],
        "started_at_unix":started,
        "finished_at_unix":time.time(),
        "external_action_performed":False,
        "financial_action_performed":False,
        "deployment_performed":False,
    }

    RESEARCH_DIR.mkdir(parents=True,exist_ok=True)
    safe=re.sub(r"[^a-z0-9]+","_",candidate_name.lower()).strip("_")[:80]
    out=RESEARCH_DIR/f"targeted_evidence_v69_22_{safe}_{int(started*1000)}.json"
    base.atomic(out,artifact)

    state={
        "healthy":True,
        "candidate_name":candidate_name,
        "requirements_requested":requirements,
        "artifact":str(out),
        "source_row_count":len(source_rows),
        "provider_summary":provider_summary,
        "rejection_summary":rejection_summary,
        "query_count":len(query_diag),
        "page_count":len(page_diag),
        "error_count":len(errors),
        "updated_at":time.time(),
    }
    base.atomic(STATE,state)
    return state
