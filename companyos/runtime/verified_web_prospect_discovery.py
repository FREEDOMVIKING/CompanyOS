from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib import request, error, parse

from companyos.runtime.stalled_stage_progression_controller import canonical_ventures
from companyos.runtime.customer_acquisition_bridge import (
    venture_copy,
    roots_for,
    find_contacts,
)

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"

STATE=RT/"verified_web_prospect_discovery_state.json"
LATEST=RT/"verified_web_prospect_discovery_latest.json"
HISTORY=RT/"verified_web_prospect_discovery_history.jsonl"

VERSION="V66.28"
OPENAI_URL="https://api.openai.com/v1/responses"
DEFAULT_MODEL=os.getenv("COMPANYOS_WEB_SEARCH_MODEL","gpt-5.6-luna")
PERSONAL_DOMAINS={
    "gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com",
    "aol.com","proton.me","protonmail.com","live.com","msn.com",
}
EMAIL_RE=re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$",re.I)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def env_file_values() -> dict[str,str]:
    out={}
    p=ROOT/".env"
    if not p.exists():
        return out
    for raw in p.read_text(errors="ignore").splitlines():
        if "=" not in raw or raw.lstrip().startswith("#"):
            continue
        k,v=raw.split("=",1)
        out[k.strip()]=v.strip().strip('"').strip("'")
    return out


def openai_key() -> str|None:
    return os.getenv("OPENAI_API_KEY") or env_file_values().get("OPENAI_API_KEY")


def output_text(resp: dict[str,Any]) -> str:
    texts=[]
    for item in resp.get("output") or []:
        if not isinstance(item,dict):
            continue
        if item.get("type")!="message":
            continue
        for content in item.get("content") or []:
            if not isinstance(content,dict):
                continue
            if content.get("type")=="output_text" and isinstance(content.get("text"),str):
                texts.append(content["text"])
    return "\n".join(texts).strip()


def parse_json_text(text: str) -> Any:
    t=text.strip()
    if t.startswith("```"):
        lines=t.splitlines()
        if lines and lines[0].startswith("```"):
            lines=lines[1:]
        if lines and lines[-1].strip()=="```":
            lines=lines[:-1]
        t="\n".join(lines).strip()
        if t.lower().startswith("json"):
            t=t[4:].lstrip()

    try:
        return json.loads(t)
    except Exception:
        pass

    starts=[x for x in (t.find("["),t.find("{")) if x>=0]
    if not starts:
        raise ValueError("no_json_in_web_search_output")
    start=min(starts)
    for end in range(len(t),start,-1):
        chunk=t[start:end].strip()
        if not chunk.endswith(("]", "}")):
            continue
        try:
            return json.loads(chunk)
        except Exception:
            continue
    raise ValueError("invalid_json_in_web_search_output")


def parse_retry_after_seconds(headers, body: str) -> float|None:
    try:
        value=headers.get("Retry-After") if headers is not None else None
        if value not in (None,""):
            return max(0.0,float(value))
    except Exception:
        pass

    text=str(body or "").lower()

    # Examples commonly returned by API rate-limit messages:
    # "try again in 2.5s", "try again in 750ms", "try again in 1m20s".
    m=re.search(r"try again in\s+([0-9.]+)\s*ms",text)
    if m:
        return float(m.group(1))/1000.0

    m=re.search(r"try again in\s+([0-9.]+)\s*s",text)
    if m:
        return float(m.group(1))

    m=re.search(
        r"try again in\s+([0-9.]+)\s*m(?:in(?:ute)?s?)?\s*([0-9.]*)\s*s?",
        text,
    )
    if m:
        minutes=float(m.group(1))
        seconds=float(m.group(2) or 0)
        return minutes*60.0+seconds

    return None

def openai_web_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    key=openai_key()
    if not key:
        return {"ok":False,"status":"OPENAI_API_KEY_MISSING"}

    audience=copy.get("audience") or "businesses that fit this product"
    live_url=copy.get("live_url") or ""
    title=copy.get("title") or cid.replace("_"," ").title()
    description=copy.get("description") or ""

    prompt = "\n".join([
        "Find up to 5 businesses that are plausible prospects for the launched venture below.",
        "",
        f"Venture: {title}",
        f"Description: {description}",
        f"Target audience: {audience}",
        f"Live product URL: {live_url}",
        "",
        "Return ONLY valid JSON in this exact shape:",
        '{"prospects":[{"company_name":"...","public_business_email":"...","official_website":"https://...","source_url":"https://...","fit_reason":"..."}]}',
        "",
        "Requirements:",
        "- The email must be a publicly listed BUSINESS contact email.",
        "- source_url must be an official company-owned page where that exact email is visible.",
        "- Prefer role-based business addresses such as sales, info, estimating, office, contact, or partnerships.",
        "- Do not infer, guess, generate, or pattern-match an email address.",
        "- Do not return private/personal contact data.",
        "- Do not use data-broker, people-search, scraped directory, social-media-profile, or lead-list pages as the source.",
        "- official_website and source_url must be public HTTP(S) URLs.",
        "- Fit must be based on the venture and target audience above.",
        '- If no qualifying prospects are found, return {"prospects":[]}.',
    ])

    max_output=max(
        500,
        min(
            int(os.getenv("COMPANYOS_WEB_SEARCH_MAX_OUTPUT_TOKENS","1200")),
            4000,
        ),
    )
    retry_ceiling=max(
        1.0,
        min(
            float(os.getenv("COMPANYOS_WEB_SEARCH_INLINE_RETRY_CEILING_SECONDS","20")),
            60.0,
        ),
    )

    body={
        "model":DEFAULT_MODEL,
        "reasoning":{"effort":"none"},
        "max_output_tokens":max_output,
        "tools":[{"type":"web_search","search_context_size":"low"}],
        "input":prompt,
    }

    attempts=[]
    for attempt in range(1,3):
        data=json.dumps(body).encode()
        req=request.Request(
            OPENAI_URL,
            data=data,
            method="POST",
            headers={
                "Authorization":f"Bearer {key}",
                "Content-Type":"application/json",
                "User-Agent":"CompanyOS/V66.30",
            },
        )

        try:
            with request.urlopen(req,timeout=90) as resp:
                raw=resp.read()
            payload=json.loads(raw.decode())
        except error.HTTPError as exc:
            err_body=exc.read().decode("utf-8","replace")
            retry_after=parse_retry_after_seconds(exc.headers,err_body)
            attempts.append({
                "attempt":attempt,
                "http_status":exc.code,
                "retry_after_seconds":retry_after,
            })

            if (
                exc.code==429
                and attempt==1
                and retry_after is not None
                and retry_after <= retry_ceiling
            ):
                # Honor the actual short API retry window instead of turning
                # a seconds-long TPM event into a 30-minute stall.
                time.sleep(max(0.5,retry_after+0.75))
                continue

            return {
                "ok":False,
                "status":f"OPENAI_HTTP_{exc.code}",
                "error":err_body[:1200],
                "retry_after_seconds":retry_after,
                "request_max_output_tokens":max_output,
                "reasoning_effort":"none",
                "attempts":attempts,
            }
        except Exception as exc:
            return {
                "ok":False,
                "status":"OPENAI_REQUEST_ERROR",
                "error":f"{type(exc).__name__}:{exc}",
                "request_max_output_tokens":max_output,
                "reasoning_effort":"none",
                "attempts":attempts,
            }

        text=output_text(payload)
        try:
            parsed=parse_json_text(text)
        except Exception as exc:
            return {
                "ok":False,
                "status":"OPENAI_OUTPUT_PARSE_ERROR",
                "error":f"{type(exc).__name__}:{exc}",
                "output_preview":text[:1200],
                "request_max_output_tokens":max_output,
                "reasoning_effort":"none",
                "attempts":attempts,
            }

        prospects=parsed.get("prospects") if isinstance(parsed,dict) else None
        if not isinstance(prospects,list):
            prospects=[]

        return {
            "ok":True,
            "status":"SEARCH_COMPLETED",
            "model":DEFAULT_MODEL,
            "response_id":payload.get("id"),
            "prospects":prospects[:5],
            "request_max_output_tokens":max_output,
            "reasoning_effort":"none",
            "attempts":attempts,
        }

    return {
        "ok":False,
        "status":"OPENAI_RETRY_EXHAUSTED",
        "attempts":attempts,
    }


ROLE_LOCALS={
    "info","sales","contact","office","hello","support","estimating",
    "estimate","bids","bid","quotes","quote","projects","project",
    "partnerships","business","inquiries","inquiry","admin","service",
    "services","customerservice","operations","ops","marketing",
}

def _provider_key(*names):
    vals=env_file_values()
    for name in names:
        value=os.getenv(name) or vals.get(name)
        if value:
            return value
    return None

def _search_query(cid: str, copy: dict[str,Any]) -> str:
    title=str(copy.get("title") or cid.replace("_"," ").title())
    audience=str(copy.get("audience") or "").strip()
    if audience:
        return f'{audience} business contact email "{title}"'
    return f'businesses that could use "{title}" contact email'

def _query_variants(cid: str, copy: dict[str,Any]) -> list[str]:
    title=str(copy.get("title") or cid.replace("_"," ").title()).strip()
    audience=str(copy.get("audience") or copy.get("target_customer") or "").strip()
    description=str(copy.get("description") or copy.get("offer") or "").strip()
    geo=str(
        copy.get("location")
        or copy.get("geography")
        or copy.get("region")
        or copy.get("market")
        or ""
    ).strip()

    stop={
        "local","software","app","application","tool","platform","service","services",
        "solution","solutions","opportunity","company","companies","business","businesses",
        "organizer","system","online","digital","mobile","workflow","marketplace",
        "the","and","for","with","from","this","that","your","our","their","into",
    }

    def useful_words(value: str, limit: int=6) -> list[str]:
        out=[]
        for token in re.findall(r"[A-Za-z0-9]+",value.lower()):
            if len(token)<4 or token in stop:
                continue
            if token not in out:
                out.append(token)
            if len(out)>=limit:
                break
        return out

    audience_words=useful_words(audience,5)
    title_words=useful_words(title+" "+description,6)

    if audience:
        audience_phrase=" ".join(audience.split())
    elif audience_words:
        audience_phrase=" ".join(audience_words)
    else:
        audience_phrase=" ".join(title_words[:3]) or cid.replace("_"," ")

    # A singular-ish variant often finds actual business homepages instead of listicles.
    singular_words=[]
    for word in audience_phrase.split():
        w=word
        if w.lower().endswith("ies") and len(w)>5:
            w=w[:-3]+"y"
        elif w.lower().endswith("s") and len(w)>5:
            w=w[:-1]
        singular_words.append(w)
    singular_phrase=" ".join(singular_words)

    geo_prefix=(geo+" ") if geo else ""
    negative="-blog -article -news -directory -template -examples"

    queries=[
        f'{geo_prefix}"{audience_phrase}" "contact us" {negative}',
        f'{geo_prefix}"{singular_phrase}" contact {negative}',
        f'{geo_prefix}"{singular_phrase}" "about us" contact {negative}',
        f'{geo_prefix}"{singular_phrase}" email contact {negative}',
        f'{geo_prefix}"{singular_phrase}" official website contact',
    ]

    core=[x for x in audience_words+title_words if x not in {"contact","email"}]
    if core:
        queries.append(f'{geo_prefix}{" ".join(core[:4])} contact {negative}')

    out=[]
    seen=set()
    for q in queries:
        q=" ".join(q.split()).strip()
        key=q.lower()
        if not q or key in seen:
            continue
        seen.add(key)
        out.append(q)
        if len(out)>=7:
            break
    return out

def _decode_ddg_url(url: str) -> str:
    try:
        parsed_url=parse.urlparse(url)
        qs=parse.parse_qs(parsed_url.query)
        uddg=qs.get("uddg")
        if uddg:
            return parse.unquote(uddg[0])
    except Exception:
        pass
    return url

def _brave_search(query: str) -> dict[str,Any]:
    key=_provider_key("COMPANYOS_BRAVE_SEARCH_API_KEY","BRAVE_SEARCH_API_KEY")
    if not key:
        return {"ok":False,"status":"BRAVE_KEY_MISSING"}

    url="https://api.search.brave.com/res/v1/web/search?"+parse.urlencode({
        "q":query,
        "count":10,
        "country":"US",
        "search_lang":"en",
    })
    req=request.Request(
        url,
        method="GET",
        headers={
            "Accept":"application/json",
            "X-Subscription-Token":key,
            "User-Agent":"CompanyOS/V66.31A",
        },
    )
    try:
        with request.urlopen(req,timeout=30) as resp:
            payload=json.loads(resp.read().decode())
    except error.HTTPError as exc:
        return {"ok":False,"status":f"BRAVE_HTTP_{exc.code}"}
    except Exception as exc:
        return {"ok":False,"status":f"BRAVE_ERROR:{type(exc).__name__}"}

    rows=[]
    for x in ((payload.get("web") or {}).get("results") or [])[:10]:
        if not isinstance(x,dict):
            continue
        u=x.get("url")
        if isinstance(u,str) and u.startswith(("http://","https://")):
            rows.append({
                "title":str(x.get("title") or "")[:300],
                "url":u,
                "snippet":str(x.get("description") or "")[:800],
            })
    return {"ok":True,"status":"BRAVE_OK","provider":"brave","results":rows}

def _ddg_search(query: str) -> dict[str,Any]:
    endpoints=[
        ("duckduckgo_html","https://html.duckduckgo.com/html/?"+parse.urlencode({"q":query})),
        ("duckduckgo_lite","https://lite.duckduckgo.com/lite/?"+parse.urlencode({"q":query})),
    ]

    rows=[]
    seen=set()
    attempts=[]
    strip_tags=re.compile(r"<[^>]+>")

    patterns=[
        re.compile(
            r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
        re.compile(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
        re.compile(
            r'<a[^>]+rel=["\']nofollow["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
        re.compile(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']nofollow["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
    ]

    for provider_name,url in endpoints:
        req=request.Request(
            url,
            method="GET",
            headers={
                "User-Agent":"Mozilla/5.0 CompanyOSProspectSearch/1.0",
                "Accept":"text/html,application/xhtml+xml",
            },
        )
        try:
            with request.urlopen(req,timeout=30) as resp:
                body=resp.read(2_000_000).decode("utf-8","replace")
        except error.HTTPError as exc:
            attempts.append({"provider":provider_name,"status":f"HTTP_{exc.code}"})
            continue
        except Exception as exc:
            attempts.append({
                "provider":provider_name,
                "status":f"ERROR:{type(exc).__name__}",
            })
            continue

        before=len(rows)
        for pattern in patterns:
            for href,title_html in pattern.findall(body):
                href=href.replace("&amp;","&")
                u=_decode_ddg_url(href)
                if not u.startswith(("http://","https://")):
                    continue
                host=parse.urlparse(u).netloc.lower()
                if "duckduckgo.com" in host:
                    continue
                if u in seen:
                    continue
                seen.add(u)
                title=" ".join(strip_tags.sub(" ",title_html).split())[:300]
                rows.append({"title":title,"url":u,"snippet":""})
                if len(rows)>=20:
                    break
            if len(rows)>=20:
                break

        attempts.append({
            "provider":provider_name,
            "status":"OK",
            "new_results":len(rows)-before,
        })
        if len(rows)>=20:
            break

    return {
        "ok":True,
        "status":"DDG_OK",
        "provider":"duckduckgo_keyless",
        "results":rows,
        "attempts":attempts,
    }

def _same_host(a: str, b: str) -> bool:
    try:
        ha=parse.urlparse(a).netloc.lower().split(":")[0]
        hb=parse.urlparse(b).netloc.lower().split(":")[0]
    except Exception:
        return False
    for name in ("www.",):
        if ha.startswith(name): ha=ha[len(name):]
        if hb.startswith(name): hb=hb[len(name):]
    return ha==hb

def _extract_candidate_emails(html_text: str) -> list[str]:
    found=set()
    text=html_text or ""
    # Visible and mailto addresses.
    for m in re.findall(r'(?i)([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})',text):
        email=m.lower().strip(".,;:()[]<>\"'")
        if not EMAIL_RE.match(email):
            continue
        domain=email.split("@",1)[1]
        local=email.split("@",1)[0].lower()
        if domain in PERSONAL_DOMAINS:
            continue
        # Only role-based mailboxes are eligible for automatic outreach.
        normalized=re.sub(r'[^a-z]','',local)
        if normalized not in ROLE_LOCALS:
            continue
        found.add(email)
    return sorted(found)

def _contact_links(page_url: str, html_text: str) -> list[str]:
    hrefs=re.findall(r"""(?i)href=["']([^"']+)["']""", html_text or "")
    out=[]
    seen=set()
    for href in hrefs:
        href=href.replace("&amp;","&")
        absolute=parse.urljoin(page_url,href)
        if not absolute.startswith(("http://","https://")):
            continue
        if not _same_host(page_url,absolute):
            continue
        low=absolute.lower()
        if not any(x in low for x in (
            "contact","about","sales","office","estimating","estimate",
            "bid","quote","service","team",
        )):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        out.append(absolute)
        if len(out)>=4:
            break
    return out

RELEVANCE_STOP={
    "local","software","app","application","tool","platform","service","services",
    "solution","solutions","opportunity","company","companies","business","businesses",
    "organizer","system","online","digital","mobile","workflow","marketplace",
    "the","and","for","with","from","this","that","your","our","their","into",
}

CONTENT_PATH_MARKERS=(
    "/blog/","/blogs/","/article/","/articles/","/news/","/resources/",
    "/resource/","/guides/","/guide/","/templates/","/template/","/terms",
    "/privacy","/careers","/jobs","/press/","/stories/","/learn/",
)

CONTENT_TITLE_MARKERS=(
    " examples"," template"," templates"," trends"," company profile",
    " pricing"," directory"," list of "," how to "," guide to "," blog ",
)

def relevance_tokens(copy: dict[str,Any]) -> list[str]:
    values=[
        str(copy.get("audience") or ""),
        str(copy.get("title") or ""),
        str(copy.get("description") or ""),
    ]
    out=[]
    for raw in re.findall(r"[A-Za-z0-9]+"," ".join(values).lower()):
        token=raw.strip()
        if len(token)<4 or token in RELEVANCE_STOP:
            continue
        if token.endswith("ies") and len(token)>5:
            token=token[:-3]+"y"
        elif token.endswith("s") and len(token)>5:
            token=token[:-1]
        if token not in out:
            out.append(token)
        if len(out)>=10:
            break
    return out

def content_like_url(url: str) -> bool:
    low=str(url or "").lower()
    return any(x in low for x in CONTENT_PATH_MARKERS)

def content_like_title(title: str) -> bool:
    low=" "+str(title or "").lower()+" "
    return any(x in low for x in CONTENT_TITLE_MARKERS)

def page_relevance(body: str, copy: dict[str,Any]) -> dict[str,Any]:
    tokens=relevance_tokens(copy)
    text=" "+re.sub(r"[^a-z0-9]+"," ",str(body or "").lower())+" "
    matched=[]
    for token in tokens:
        if f" {token} " in text or f" {token}s " in text:
            matched.append(token)
    required=1 if tokens else 0
    return {
        "ok":len(matched)>=required,
        "tokens":tokens,
        "matched":matched,
        "required":required,
    }

def _find_business_email_on_site(result: dict[str,Any], copy: dict[str,Any]) -> dict[str,Any]|None:
    start=result.get("url")
    if not isinstance(start,str) or not start.startswith(("http://","https://")):
        return None

    parsed_start=parse.urlparse(start)
    if not parsed_start.netloc:
        return None

    site_root=f"{parsed_start.scheme}://{parsed_start.netloc}/"

    root=fetch_source(site_root)
    if not root.get("ok"):
        return None

    root_body=root.get("text") or ""
    rel=page_relevance(root_body,copy)
    if not rel["ok"]:
        return None

    queue=[site_root]
    visited=set()

    if (
        not content_like_url(result.get("url") or "")
        and result.get("url")!=site_root
        and not content_like_title(str(result.get("title") or ""))
    ):
        queue.append(result["url"])

    for link in _contact_links(site_root,root_body):
        if link not in queue and not content_like_url(link):
            queue.append(link)

    while queue and len(visited)<8:
        url=queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        fetched=root if url==site_root else fetch_source(url)
        if not fetched.get("ok"):
            continue

        final_url=fetched.get("final_url") or url
        if content_like_url(final_url):
            continue

        body=fetched.get("text") or ""
        emails=_extract_candidate_emails(body)
        if emails:
            email=emails[0]
            if not same_company_domain(email,site_root):
                continue
            return {
                "company_name":str(result.get("title") or parsed_start.netloc)[:200],
                "public_business_email":email,
                "official_website":site_root,
                "source_url":final_url,
                "fit_reason":str(result.get("snippet") or "Matched by public business search.")[:500],
                "relevance_verified":True,
                "relevance_tokens":rel["tokens"],
                "matched_relevance_tokens":rel["matched"],
                "source_is_content_page":False,
            }

        for link in _contact_links(final_url,body):
            if link not in visited and link not in queue and not content_like_url(link):
                queue.append(link)

    return None

SEARCH_INTERMEDIARY_HOSTS={
    "linkedin.com","www.linkedin.com","facebook.com","www.facebook.com",
    "instagram.com","www.instagram.com","x.com","twitter.com","www.twitter.com",
    "youtube.com","www.youtube.com","yelp.com","www.yelp.com",
    "yellowpages.com","www.yellowpages.com","angi.com","www.angi.com",
    "homeadvisor.com","www.homeadvisor.com","bbb.org","www.bbb.org",
    "crunchbase.com","www.crunchbase.com","pitchbook.com","www.pitchbook.com",
    "clutch.co","www.clutch.co","g2.com","www.g2.com",
    "capterra.com","www.capterra.com",
}

def _host_words(host: str) -> set[str]:
    return {
        x for x in re.findall(r"[a-z0-9]+",str(host or "").lower())
        if len(x)>=4 and x not in {"www","com","net","org","co"}
    }

def rank_search_candidates(rows: list[dict[str,Any]], copy: dict[str,Any]) -> list[dict[str,Any]]:
    target=set(relevance_tokens(copy))
    by_host={}

    for row in rows:
        url=str(row.get("url") or "")
        if not url.startswith(("http://","https://")):
            continue
        parsed=parse.urlparse(url)
        host=parsed.netloc.lower().split(":",1)[0]
        if not host or host in SEARCH_INTERMEDIARY_HOSTS:
            continue
        if content_like_url(url) or content_like_title(str(row.get("title") or "")):
            continue

        title_words={
            x for x in re.findall(r"[a-z0-9]+",str(row.get("title") or "").lower())
            if len(x)>=4
        }
        host_words=_host_words(host)
        matches=target.intersection(title_words.union(host_words))
        path=parsed.path or "/"
        depth=len([x for x in path.split("/") if x])
        rootish=depth<=1

        score=0
        score += 5 if rootish else max(0,3-depth)
        score += min(9,3*len(matches))
        if any(x in title_words for x in {"construction","contractor","builder","company","group"}):
            score += 2
        if "contact" in title_words:
            score += 1

        candidate={**row,"candidate_score":score,"candidate_host":host,"target_matches":sorted(matches)}
        prev=by_host.get(host)
        if prev is None or candidate["candidate_score"]>prev["candidate_score"]:
            by_host[host]=candidate

    ranked=sorted(
        by_host.values(),
        key=lambda x:(int(x.get("candidate_score") or 0),-len(parse.urlparse(x.get("url") or "").path)),
        reverse=True,
    )
    return ranked

def provider_fallback_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    queries=_query_variants(cid,copy)
    attempts=[]
    aggregated=[]
    seen_urls=set()

    providers=[]
    if _provider_key("COMPANYOS_BRAVE_SEARCH_API_KEY","BRAVE_SEARCH_API_KEY"):
        providers.append(("brave",_brave_search))
    providers.append(("duckduckgo_keyless",_ddg_search))

    for query in queries:
        for name,fn in providers:
            result=fn(query)
            attempts.append({
                "provider":name,
                "query":query,
                "status":result.get("status"),
                "result_count":len(result.get("results") or []),
                "sub_attempts":result.get("attempts"),
            })
            if not result.get("ok"):
                continue
            for row in result.get("results") or []:
                u=row.get("url")
                if not isinstance(u,str) or u in seen_urls:
                    continue
                seen_urls.add(u)
                aggregated.append(row)

        ranked_now=rank_search_candidates(aggregated,copy)
        # Two useful query passes are enough when we already have a diverse official-site pool.
        if len(ranked_now)>=36 and len(attempts)>=2:
            break

    ranked=rank_search_candidates(aggregated,copy)
    prospects=[]
    seen_emails=set()
    crawled=0
    rejected=0

    for row in ranked[:36]:
        prospect=_find_business_email_on_site(row,copy)
        crawled += 1
        if not prospect:
            rejected += 1
            continue
        email=prospect["public_business_email"].lower()
        if email in seen_emails:
            continue
        seen_emails.add(email)
        prospects.append(prospect)
        if len(prospects)>=5:
            break

    return {
        "ok":True,
        "status":"SEARCH_COMPLETED",
        "model":"target_aware_official_site_search_v1",
        "response_id":None,
        "prospects":prospects,
        "provider_attempts":attempts,
        "queries":queries,
        "search_candidate_count_raw":len(aggregated),
        "search_candidate_count_ranked":len(ranked),
        "sites_crawled":crawled,
        "relevance_rejected":rejected,
        "candidate_hosts_preview":[x.get("candidate_host") for x in ranked[:10]],
    }

def web_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    primary=openai_web_search(cid,copy)
    if primary.get("ok"):
        primary["selected_provider"]="openai_web"
        return primary

    status=str(primary.get("status") or "")
    if status=="OPENAI_HTTP_429" or status in {
        "OPENAI_REQUEST_ERROR",
        "OPENAI_RETRY_EXHAUSTED",
    }:
        fallback=provider_fallback_search(cid,copy)
        fallback["openai_primary_status"]=status
        fallback["openai_retry_after_seconds"]=primary.get("retry_after_seconds")
        fallback["selected_provider"]=fallback.get("model")
        return fallback

    return primary

def normalize_url(v: Any) -> str|None:
    if not isinstance(v,str):
        return None
    s=v.strip()
    if not s.startswith(("http://","https://")):
        return None
    try:
        u=parse.urlparse(s)
    except Exception:
        return None
    if not u.netloc:
        return None
    return s


def fetch_source(url: str) -> dict[str,Any]:
    req=request.Request(
        url,
        method="GET",
        headers={
            "User-Agent":"Mozilla/5.0 CompanyOSContactVerification/1.0",
            "Accept":"text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
        },
    )
    try:
        with request.urlopen(req,timeout=15) as resp:
            raw=resp.read(2_000_000)
            final_url=resp.geturl()
            ctype=resp.headers.get("content-type","")
        return {
            "ok":True,
            "status":"FETCH_OK",
            "final_url":final_url,
            "content_type":ctype,
            "text":raw.decode("utf-8","replace"),
        }
    except error.HTTPError as exc:
        return {"ok":False,"status":f"HTTP_{exc.code}"}
    except Exception as exc:
        return {"ok":False,"status":f"FETCH_ERROR:{type(exc).__name__}"}


def same_company_domain(email: str, website: str|None) -> bool:
    if not website:
        return False
    try:
        w=parse.urlparse(website).netloc.lower().split(":")[0]
    except Exception:
        return False
    if w.startswith("www."):
        w=w[4:]
    domain=email.split("@",1)[1].lower()
    return domain==w or w.endswith("."+domain) or domain.endswith("."+w)


def verify_prospect(raw: dict[str,Any], copy: dict[str,Any]|None=None) -> dict[str,Any]:
    company=str(raw.get("company_name") or "").strip()[:200]
    email=str(raw.get("public_business_email") or "").strip().lower()
    website=normalize_url(raw.get("official_website"))
    source=normalize_url(raw.get("source_url"))
    fit=str(raw.get("fit_reason") or "").strip()[:500]

    reasons=[]
    if not company:
        reasons.append("company_missing")
    if not EMAIL_RE.match(email):
        reasons.append("email_invalid")
    elif email.split("@",1)[1] in PERSONAL_DOMAINS:
        reasons.append("personal_email_domain")
    if not website:
        reasons.append("official_website_missing_or_invalid")
    if not source:
        reasons.append("source_url_missing_or_invalid")
    if source and content_like_url(source):
        reasons.append("content_or_policy_source_page")

    fetch=None
    rel=None
    if not reasons and source:
        fetch=fetch_source(source)
        if not fetch.get("ok"):
            reasons.append("source_fetch_failed")
        else:
            body=(fetch.get("text") or "").lower()
            if email.lower() not in body:
                reasons.append("exact_email_not_visible_on_source")
            if copy:
                home=fetch_source(website)
                if not home.get("ok"):
                    reasons.append("official_homepage_fetch_failed")
                else:
                    rel=page_relevance(home.get("text") or "",copy)
                    if not rel["ok"]:
                        reasons.append("target_audience_relevance_not_proven")

    domain_match=same_company_domain(email,website) if EMAIL_RE.match(email) else False
    if EMAIL_RE.match(email) and website and not domain_match:
        reasons.append("email_domain_does_not_match_official_site")

    if raw.get("relevance_verified") is False:
        reasons.append("upstream_relevance_rejected")

    return {
        "ok":not reasons,
        "company_name":company,
        "business_email":email,
        "official_website":website,
        "source_url":source,
        "fit_reason":fit,
        "email_domain_matches_official_site":domain_match,
        "source_fetch_status":(fetch or {}).get("status"),
        "relevance_verified":not reasons if copy else bool(raw.get("relevance_verified",False)),
        "relevance_tokens":(rel or {}).get("tokens") or raw.get("relevance_tokens") or [],
        "matched_relevance_tokens":(rel or {}).get("matched") or raw.get("matched_relevance_tokens") or [],
        "reasons":reasons,
    }


def result_path(cid: str) -> Path|None:
    roots=roots_for(cid)
    if not roots:
        return None
    d=roots[0]/"companyos_progress"
    d.mkdir(parents=True,exist_ok=True)
    return d/"verified_prospect_contacts.jsonl"


def recent_meaningful_result(cid: str) -> dict[str,Any]|None:
    if not HISTORY.exists():
        return None

    latest=None
    try:
        lines=HISTORY.read_text(errors="ignore").splitlines()[-200:]
    except Exception:
        return None

    for line in lines:
        try:
            row=json.loads(line)
        except Exception:
            continue
        if not isinstance(row,dict):
            continue
        for result in row.get("results") or []:
            if not isinstance(result,dict):
                continue
            if str(result.get("canonical_id") or "")!=str(cid):
                continue
            if result.get("status")=="SEARCH_COOLDOWN":
                continue
            latest={
                "timestamp_unix":row.get("timestamp_unix"),
                **result,
            }
    return latest


def retry_delay_for_result(result: dict[str,Any]|None) -> int:
    if not result:
        return 0

    status=str(result.get("status") or "")

    if status=="DISCOVERY_COMPLETED":
        verified=int(result.get("verified_count") or 0)
        candidates=int(result.get("search_candidate_count") or 0)

        if verified>0:
            return max(
                1800,
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_SUCCESS_COOLDOWN_SECONDS",
                    "21600",
                )),
            )

        if candidates>0:
            return max(
                300,
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_REJECTED_COOLDOWN_SECONDS",
                    "900",
                )),
            )

        return max(
            300,
            int(os.getenv(
                "COMPANYOS_PROSPECT_DISCOVERY_EMPTY_COOLDOWN_SECONDS",
                "1800",
            )),
        )

    if status=="OPENAI_HTTP_429":
        api_retry=result.get("retry_after_seconds")
        try:
            if api_retry is not None:
                return max(5,min(int(float(api_retry)+5),300))
        except Exception:
            pass

        # If an older V66.29 result has only the raw API error text, recover
        # retry timing from that instead of defaulting to 30 minutes.
        parsed=parse_retry_after_seconds(None,str(result.get("error") or ""))
        if parsed is not None:
            return max(5,min(int(parsed+5),300))

        return max(
            30,
            min(
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_RATE_LIMIT_BACKOFF_SECONDS",
                    "60",
                )),
                300,
            ),
        )

    if status.startswith("OPENAI_HTTP_"):
        return max(
            60,
            min(
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_HTTP_ERROR_BACKOFF_SECONDS",
                    "300",
                )),
                900,
            ),
        )

    if status in {
        "OPENAI_REQUEST_ERROR",
        "OPENAI_OUTPUT_PARSE_ERROR",
        "OPENAI_API_KEY_MISSING",
        "OPENAI_RETRY_EXHAUSTED",
    }:
        return max(
            60,
            min(
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_ERROR_BACKOFF_SECONDS",
                    "300",
                )),
                900,
            ),
        )

    return 300

def run_once() -> dict[str,Any]:
    state=load_json(STATE,{
        "last_search_by_venture":{},
        "last_outcome_by_venture":{},
    })
    last=state.setdefault("last_search_by_venture",{})
    outcomes=state.setdefault("last_outcome_by_venture",{})

    now=time.time()
    results=[]
    total_verified=0

    for cid,row in sorted(canonical_ventures().items()):
        if str(row.get("stage") or "")!="LAUNCH":
            continue

        existing=find_contacts(cid)
        if existing:
            results.append({
                "canonical_id":cid,
                "status":"VERIFIED_CONTACTS_ALREADY_AVAILABLE",
                "existing_contact_count":len(existing),
                "last_meaningful_result":recent_meaningful_result(cid),
            })
            continue

        prior=outcomes.get(cid)
        if not isinstance(prior,dict):
            prior=recent_meaningful_result(cid)

        previous=float(last.get(cid,0) or 0)
        delay=retry_delay_for_result(prior)

        if previous and now-previous < delay:
            results.append({
                "canonical_id":cid,
                "status":"SEARCH_COOLDOWN",
                "cooldown_seconds":delay,
                "cooldown_remaining_seconds":int(delay-(now-previous)),
                "last_meaningful_result":prior,
            })
            continue

        copy=venture_copy(cid)
        search=web_search(cid,copy)

        search_result={
            "canonical_id":cid,
            "status":search.get("status"),
            "error":search.get("error"),
        }

        if not search.get("ok"):
            # Failed searches now get a short, status-specific backoff rather
            # than being treated like a successful 6-hour search.
            last[cid]=now
            outcomes[cid]=search_result
            results.append(search_result)
            break

        verified=[]
        rejected=[]
        for raw in search.get("prospects") or []:
            if not isinstance(raw,dict):
                continue
            check=verify_prospect(raw,copy)
            if check["ok"]:
                verified.append(check)
            else:
                rejected.append(check)

        p=result_path(cid)
        if p:
            existing_emails=set()
            if p.exists():
                for line in p.read_text(errors="ignore").splitlines():
                    try:
                        old=json.loads(line)
                    except Exception:
                        continue
                    if isinstance(old,dict) and old.get("business_email"):
                        existing_emails.add(str(old["business_email"]).lower())

            for v in verified:
                if v["business_email"].lower() in existing_emails:
                    continue
                append_jsonl(p,{
                    "schema":"companyos.verified_public_business_prospect.v1",
                    "version":VERSION,
                    "canonical_id":cid,
                    "company_name":v["company_name"],
                    "business_email":v["business_email"],
                    "official_website":v["official_website"],
                    "source_url":v["source_url"],
                    "fit_reason":v["fit_reason"],
                    "email_domain_matches_official_site":v["email_domain_matches_official_site"],
                    "source_fetch_status":v["source_fetch_status"],
                    "relevance_verified":v.get("relevance_verified") is True,
                    "relevance_tokens":v.get("relevance_tokens") or [],
                    "matched_relevance_tokens":v.get("matched_relevance_tokens") or [],
                    "verified_at_unix":time.time(),
                    "contact_method":"public_business_email",
                    "personal_contact_inferred":False,
                })
                existing_emails.add(v["business_email"].lower())

        total_verified += len(verified)

        search_result={
            "canonical_id":cid,
            "status":"DISCOVERY_COMPLETED",
            "model":search.get("model"),
            "response_id":search.get("response_id"),
            "search_candidate_count":len(search.get("prospects") or []),
            "verified_count":len(verified),
            "rejected_count":len(rejected),
            "verified":[
                {
                    "company_name":x["company_name"],
                    "email_domain":x["business_email"].split("@",1)[1],
                    "official_website":x["official_website"],
                    "source_url":x["source_url"],
                    "fit_reason":x["fit_reason"],
                }
                for x in verified
            ],
            "rejected":[
                {
                    "company_name":x.get("company_name"),
                    "email_domain":(
                        x.get("business_email","").split("@",1)[1]
                        if "@" in x.get("business_email","") else None
                    ),
                    "reasons":x.get("reasons"),
                    "source_fetch_status":x.get("source_fetch_status"),
                }
                for x in rejected
            ],
        }

        last[cid]=now
        outcomes[cid]=search_result
        results.append(search_result)
        break

    save_json(STATE,{
        "version":VERSION,
        "updated_at_unix":time.time(),
        "last_search_by_venture":last,
        "last_outcome_by_venture":outcomes,
    })

    report={
        "version":"V66.34",
        "mode":"adaptive_web_prospect_search_backoff",
        "model":DEFAULT_MODEL,
        "openai_key_present":bool(openai_key()),
        "verified_contacts_created":total_verified,
        "results":results,
        "rules":{
            "successful_verified_search_long_cooldown":True,
            "empty_search_shorter_retry":True,
            "rejected_candidates_shorter_retry":True,
            "failed_search_short_backoff":True,
            "last_meaningful_result_preserved":True,
            "one_web_search_per_run":True,
            "exact_email_visible_on_source_required":True,
            "official_public_source_required":True,
            "personal_email_domains_rejected":True,
            "personal_contact_inference":False,
            "financial_actions":False,
            "authority_switches_changed":False,
        },
        "timestamp_unix":time.time(),
    }

    save_json(LATEST,report)
    append_jsonl(HISTORY,report)
    return report
