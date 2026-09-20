from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

RT=Path.home()/".companyos_runtime"/"procurement"
AUDIT=RT/"official_vendor_verifications.jsonl"
LATEST=RT/"official_vendor_verification_latest.json"
RT.mkdir(parents=True,exist_ok=True)

VERSION="V66.10"
TIMEOUT=15
MAX_HTML_BYTES=1_500_000

# These are discovery/media/community/aggregation surfaces, not the merchant
# whose checkout should become payment authority.
DENY_DOMAINS={
    "yahoo.com","finance.yahoo.com","news.yahoo.com",
    "google.com","bing.com","duckduckgo.com",
    "forbes.com","reuters.com","bloomberg.com","cnbc.com","wsj.com",
    "medium.com","substack.com",
    "reddit.com","quora.com",
    "facebook.com","instagram.com","x.com","twitter.com","tiktok.com",
    "youtube.com","linkedin.com",
    "wikipedia.org","github.com",
}

GENERIC_WORDS={
    "official","current","pricing","price","prices","purchase","buy","vendor",
    "provider","supplier","software","opportunity","requirement","requirements",
    "service","services","marketplace","product","products","solution","solutions",
    "app","application","platform","company","business","best","cheap","cheapest",
}

EDITORIAL_PATH_MARKERS=(
    "/blog/","/blogs/","/news/","/article/","/articles/","/learn/",
    "/guide/","/guides/","/resources/","/research/","/press/","/insights/",
)

CATEGORY_CUES={
    "domain":{"domain","registration","registrar","renewal","transfer","year"},
    "hosting":{"hosting","server","cloud","bandwidth","storage","month","plan"},
    "software_api":{"api","developer","requests","credits","subscription","plan","month"},
    "inventory_product":{"inventory","wholesale","supplier","unit","case","pack","minimum"},
    "contractor_service":{"service","quote","hour","project","contractor","estimate"},
    "materials_equipment":{"equipment","rental","material","day","week","month","unit"},
    "advertising":{"advertising","campaign","click","cpc","impression","budget"},
    "general_procurement":{"pricing","price","plan","order","purchase"},
}

PRICE_RE=re.compile(
    r"(?:(?:USD|US\$)\s*|\$\s*)([0-9]{1,7}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)",
    re.I,
)

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self.skip=0
        self.title=[]
        self.in_title=False
    def handle_starttag(self,tag,attrs):
        t=tag.lower()
        if t in {"script","style","noscript","svg","template"}:
            self.skip+=1
        if t=="title":
            self.in_title=True
    def handle_endtag(self,tag):
        t=tag.lower()
        if t in {"script","style","noscript","svg","template"} and self.skip:
            self.skip-=1
        if t=="title":
            self.in_title=False
    def handle_data(self,data):
        if self.skip:
            return
        s=" ".join(str(data).split())
        if not s:
            return
        self.parts.append(s)
        if self.in_title:
            self.title.append(s)

def norm_domain(url_or_domain: str|None) -> str:
    if not url_or_domain:
        return ""
    s=str(url_or_domain).strip().lower()
    if "://" in s:
        try:
            s=urllib.parse.urlparse(s).hostname or ""
        except Exception:
            return ""
    return s.split(":")[0].strip(".").removeprefix("www.")

def registrableish(domain: str) -> str:
    # Sufficient for vendor/source matching here. It intentionally does not
    # attempt to replace a full public-suffix database.
    parts=norm_domain(domain).split(".")
    if len(parts)<=2:
        return ".".join(parts)
    common_second={"co","com","net","org","gov","ac"}
    if len(parts)>=3 and parts[-2] in common_second and len(parts[-1])==2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])

def same_site(a: str,b: str) -> bool:
    aa=registrableish(a); bb=registrableish(b)
    return bool(aa and bb and aa==bb)

def denied(domain: str) -> bool:
    d=norm_domain(domain)
    return any(d==x or d.endswith("."+x) for x in DENY_DOMAINS)

def tokens(text: str|None) -> list[str]:
    vals=re.findall(r"[a-z0-9]{3,}",str(text or "").lower())
    out=[]
    for x in vals:
        if x in GENERIC_WORDS:
            continue
        if x not in out:
            out.append(x)
    return out[:12]

def fetch_page(url: str) -> dict[str,Any]:
    req=urllib.request.Request(
        url,
        headers={
            "User-Agent":"Mozilla/5.0 CompanyOS/66.10",
            "Accept":"text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
        raw=r.read(MAX_HTML_BYTES)
        ctype=str(r.headers.get("Content-Type") or "")
        final=r.geturl()
        status=getattr(r,"status",200)
    if "html" not in ctype.lower() and not raw.lstrip().startswith((b"<",b"<!")):
        return {
            "ok":False,
            "status":"not_html",
            "http_status":status,
            "final_url":final,
            "content_type":ctype,
        }
    text=raw.decode(errors="ignore")
    parser=VisibleText()
    try:
        parser.feed(text)
    except Exception:
        pass
    visible=" ".join(parser.parts)
    visible=" ".join(html.unescape(visible).split())
    title=" ".join(parser.title)
    return {
        "ok":True,
        "http_status":status,
        "final_url":final,
        "domain":norm_domain(final),
        "title":title[:500],
        "text":visible[:250000],
    }

def _price_candidates(text: str, item_tokens: list[str], category: str) -> list[dict[str,Any]]:
    low=text.lower()
    cues=CATEGORY_CUES.get(category,CATEGORY_CUES["general_procurement"])
    rows=[]
    for m in PRICE_RE.finditer(text):
        try:
            value=float(m.group(1).replace(",",""))
        except Exception:
            continue
        if value<=0 or value>1_000_000:
            continue
        lo=max(0,m.start()-260)
        hi=min(len(text),m.end()+260)
        window=text[lo:hi]
        wlow=window.lower()
        item_hits=sum(1 for t in item_tokens if t in wlow)
        cue_hits=sum(1 for t in cues if t in wlow)
        pricing_hits=sum(1 for t in ("price","pricing","plan","per ","/month","/year","monthly","annually","renew","registration","buy","order") if t in wlow)
        score=item_hits*3+cue_hits+pricing_hits
        rows.append({
            "value_usd":value,
            "context":window[:600],
            "item_hits":item_hits,
            "category_cue_hits":cue_hits,
            "pricing_hits":pricing_hits,
            "score":score,
        })
    rows.sort(key=lambda x:(-x["score"],x["value_usd"]))
    return rows[:20]

def verify_result(
    evidence: dict[str,Any],
    *,
    item: str,
    category: str,
    known_vendor: str|None=None,
) -> dict[str,Any]:
    url=str(evidence.get("url") or "")
    search_domain=norm_domain(evidence.get("domain") or url)
    base={
        "version":VERSION,
        "timestamp_unix":time.time(),
        "url":url,
        "search_domain":search_domain,
        "official_vendor_verified":False,
        "official_price_verified":False,
        "eligible_for_vendor_selection":False,
        "reasons":[],
    }

    if not url.startswith(("http://","https://")):
        return {**base,"reasons":["invalid_url"]}
    if denied(search_domain):
        return {**base,"reasons":["aggregator_or_nonmerchant_domain"]}

    try:
        page=fetch_page(url)
    except Exception as exc:
        return {**base,"reasons":[f"fetch_failed:{type(exc).__name__}"]}

    if not page.get("ok"):
        return {**base,"reasons":[str(page.get("status") or "fetch_not_usable")]}

    final_domain=norm_domain(page.get("domain"))
    if denied(final_domain):
        return {**base,"final_domain":final_domain,"reasons":["redirected_to_nonmerchant_domain"]}
    if not same_site(search_domain,final_domain):
        return {**base,"final_domain":final_domain,"reasons":["cross_site_redirect"]}

    text=str(page.get("text") or "")
    title=str(page.get("title") or "")
    low=(title+" "+text[:120000]).lower()
    item_tokens=tokens(item)
    cues=CATEGORY_CUES.get(category,CATEGORY_CUES["general_procurement"])

    item_hits=[t for t in item_tokens if t in low]
    cue_hits=[t for t in cues if t in low]

    # A known vendor is stricter: its supplied name/domain must agree with the
    # retrieved site. Otherwise the source must at least look like a merchant
    # pricing/product page rather than editorial coverage.
    known_ok=True
    if known_vendor:
        kv=norm_domain(known_vendor)
        kv_words=tokens(known_vendor)
        known_ok=(
            (kv and same_site(kv,final_domain))
            or any(w in low[:5000] for w in kv_words)
        )

    path=urllib.parse.urlparse(str(page.get("final_url") or url)).path.lower()
    editorial_path=any(x in path for x in EDITORIAL_PATH_MARKERS)
    commercial_path=(not editorial_path) and any(x in path for x in (
        "pricing","plans","product","products","domain","domains","hosting",
        "api","shop","store","order","buy","register","subscription",
    ))
    page_commercial=(not editorial_path) and (
        commercial_path or any(x in low[:15000] for x in (
            "pricing","choose a plan","buy now","add to cart","per month","per year",
            "domain registration","api pricing","subscription",
        ))
    )

    relevance=bool(item_hits or cue_hits)
    official=bool(known_ok and relevance and page_commercial)

    prices=_price_candidates(text,item_tokens,category)
    verified_price=None
    price_record=None
    if official:
        for row in prices:
            # Tie the number to the requested item/category rather than taking
            # the first currency figure found anywhere on the page.
            if row["item_hits"]>0 or row["category_cue_hits"]>0:
                if row["pricing_hits"]>0 or row["score"]>=3:
                    verified_price=row["value_usd"]
                    price_record=row
                    break

    reasons=[]
    if not known_ok:
        reasons.append("known_vendor_mismatch")
    if not relevance:
        reasons.append("requested_item_or_category_not_found")
    if editorial_path:
        reasons.append("editorial_or_blog_path")
    if not page_commercial:
        reasons.append("page_not_commercial_pricing_surface")
    if official and verified_price is None:
        reasons.append("price_not_tied_to_requested_item")
    if official and verified_price is not None:
        reasons.append("official_vendor_and_contextual_price_verified")

    return {
        **base,
        "final_url":page.get("final_url"),
        "final_domain":final_domain,
        "page_title":title,
        "item_tokens":item_tokens,
        "item_hits":item_hits,
        "category_cue_hits":cue_hits,
        "commercial_page":page_commercial,
        "official_vendor_verified":official,
        "official_price_verified":verified_price is not None,
        "verified_price_usd":verified_price,
        "verified_price_context":price_record.get("context") if price_record else None,
        "eligible_for_vendor_selection":bool(official and verified_price is not None),
        "reasons":reasons,
    }

def verify_search_results(
    evidence_rows: list[dict[str,Any]],
    *,
    item: str,
    category: str,
    known_vendor: str|None=None,
) -> dict[str,Any]:
    verifications=[]
    for er in evidence_rows[:8]:
        v=verify_result(
            er,
            item=item,
            category=category,
            known_vendor=known_vendor,
        )
        verifications.append(v)
        append_jsonl(AUDIT,{
            "schema":"companyos.official_vendor_verification.v1",
            "item":item,
            "category":category,
            "known_vendor":known_vendor,
            **v,
        })

    eligible=[x for x in verifications if x.get("eligible_for_vendor_selection")]

    # Collapse duplicate result URLs from the same provider site.
    providers={}
    for x in eligible:
        dom=registrableish(str(x.get("final_domain") or ""))
        if not dom:
            continue
        old=providers.get(dom)
        if old is None or float(x["verified_price_usd"]) < float(old["verified_price_usd"]):
            providers[dom]=x

    compared=sorted(
        providers.values(),
        key=lambda x:(float(x["verified_price_usd"]),str(x.get("final_domain") or "")),
    )

    specific_vendor=bool(known_vendor)
    comparison_required=not specific_vendor
    comparison_satisfied=bool(compared) if specific_vendor else len(compared)>=2

    chosen=compared[0] if comparison_satisfied and compared else None

    result={
        "version":VERSION,
        "item":item,
        "category":category,
        "known_vendor":known_vendor,
        "verification_count":len(verifications),
        "verified_provider_count":len(compared),
        "comparison_required":comparison_required,
        "comparison_satisfied":comparison_satisfied,
        "chosen":chosen,
        "providers":[
            {
                "vendor_domain":x.get("final_domain"),
                "price_usd":x.get("verified_price_usd"),
                "source_url":x.get("final_url"),
                "page_title":x.get("page_title"),
            }
            for x in compared
        ],
        "rejected":[
            {
                "domain":x.get("search_domain"),
                "url":x.get("url"),
                "reasons":x.get("reasons"),
            }
            for x in verifications
            if not x.get("eligible_for_vendor_selection")
        ],
    }
    save_json(LATEST,result)
    return result

def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")

def save_json(path: Path,data: Any) -> None:
    import os,tempfile
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp): os.unlink(tmp)
        except Exception:
            pass
