from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

RUNTIME = Path.home() / ".companyos_runtime"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"
RESEARCH_DIR = RUNTIME / "canonical_research_outputs"
STATE = RUNTIME / "targeted_public_evidence_research_state.json"

TIMEOUT = max(4, int(os.getenv("COMPANYOS_TARGETED_RESEARCH_TIMEOUT_SECONDS", "10")))
MAX_SEARCH_RESULTS = max(2, int(os.getenv("COMPANYOS_TARGETED_RESEARCH_RESULTS_PER_QUERY", "5")))
MAX_PAGES_PER_REQUIREMENT = max(2, int(os.getenv("COMPANYOS_TARGETED_RESEARCH_MAX_PAGES_PER_REQUIREMENT", "8")))
MAX_EVIDENCE_PER_REQUIREMENT = max(1, int(os.getenv("COMPANYOS_TARGETED_RESEARCH_MAX_EVIDENCE_PER_REQUIREMENT", "4")))

BLOCKED_DOMAINS = {
    "duckduckgo.com",
    "google.com",
    "bing.com",
    "yahoo.com",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
}

STOPWORDS = {
    "about","after","against","automation","being","before","between","business",
    "candidate","company","could","customer","evidence","first","from","have",
    "into","market","more","other","regional","research","service","software",
    "their","there","these","this","through","using","with","would",
}

REQ_TERMS = {
    "pricing": {
        "price","prices","pricing","cost","costs","fee","fees","plan","plans",
        "subscription","monthly","annual","yearly","quote","quoted","paid","pay",
        "dollar","usd",
    },
    "buyer_demand": {
        "buyer","buyers","customer","customers","client","clients","demand",
        "adoption","adopted","users","user","case study","case studies",
        "testimonial","testimonials","contractor","contractors","used by",
    },
}


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script","style","noscript","svg"):
            self.skip += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script","style","noscript","svg") and self.skip:
            self.skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self.skip:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self._in_title and len(self.title) < 500:
            self.title = (self.title + " " + text).strip()
        self.parts.append(text)


def load(path: Path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def candidate_payload(candidate_name: str) -> tuple[Path | None, dict[str, Any]]:
    target = norm(candidate_name)
    if not CANDIDATE_DIR.exists():
        return None, {}
    for path in CANDIDATE_DIR.glob("*.json"):
        data = load(path, {})
        if not isinstance(data, dict):
            continue
        name = norm(data.get("name") or data.get("candidate_name") or data.get("venture_name") or path.stem)
        if name == target:
            return path, data
    return None, {}


def candidate_terms(candidate: dict[str, Any], fallback_name: str = "") -> list[str]:
    values = [
        candidate.get("market"),
        candidate.get("sector"),
        candidate.get("target_customer"),
        candidate.get("problem"),
        candidate.get("offer"),
        candidate.get("business_model"),
        fallback_name,
    ]
    scores: dict[str, int] = {}
    for value in values:
        for token in re.findall(r"[a-z0-9]+", norm(value)):
            if len(token) < 4 or token in STOPWORDS:
                continue
            scores[token] = scores.get(token, 0) + 1
    return [k for k, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))][:12]


def compact_phrase(value: Any, limit: int = 7) -> str:
    words = [x for x in re.findall(r"[a-z0-9]+", norm(value)) if len(x) > 2]
    return " ".join(words[:limit])


def build_queries(candidate: dict[str, Any], requirement: str) -> list[str]:
    market = compact_phrase(candidate.get("market") or candidate.get("sector") or "business")
    buyer = compact_phrase(candidate.get("target_customer") or "business customer")
    offer = compact_phrase(candidate.get("offer") or candidate.get("problem") or market)

    if requirement == "pricing":
        raw = [
            f'"{market}" "{offer}" pricing',
            f'"{buyer}" estimating software pricing',
            f'"{market}" bid workflow software cost',
            f'"{market}" contractor software pricing plans',
        ]
    elif requirement == "buyer_demand":
        raw = [
            f'"{market}" "{offer}" customers case study',
            f'"{buyer}" estimating software customers',
            f'"{market}" contractor software adoption',
            f'"{market}" bid software customer testimonials',
        ]
    else:
        raw = [f'"{market}" "{offer}" {requirement.replace("_"," ")}']

    out = []
    seen = set()
    for q in raw:
        q = re.sub(r"\s+", " ", q).strip()
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


def _request(url: str, max_bytes: int = 900_000) -> tuple[str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 CompanyOS-TargetedResearch/1.0",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        ctype = str(response.headers.get("Content-Type") or "")
        raw = response.read(max_bytes)
    return raw.decode("utf-8", "replace"), ctype


def _unwrap_duckduckgo(href: str) -> str:
    href = html.unescape(href or "")
    if href.startswith("//"):
        href = "https:" + href
    parsed = urllib.parse.urlparse(href)
    if "duckduckgo.com" in parsed.netloc:
        qs = urllib.parse.parse_qs(parsed.query)
        if qs.get("uddg"):
            return urllib.parse.unquote(qs["uddg"][0])
    return href


def search_duckduckgo(query: str) -> list[dict[str, str]]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    body, _ = _request(url, 750_000)

    pattern = re.compile(
        r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        re.I | re.S,
    )
    results = []
    seen = set()
    for href, raw_title in pattern.findall(body):
        link = _unwrap_duckduckgo(href)
        if not link.startswith(("http://","https://")):
            continue
        domain = urllib.parse.urlparse(link).netloc.lower().split(":")[0]
        domain = domain[4:] if domain.startswith("www.") else domain
        if not domain or domain in BLOCKED_DOMAINS:
            continue
        if link in seen:
            continue
        seen.add(link)
        title = re.sub(r"<[^>]+>", " ", raw_title)
        title = re.sub(r"\s+", " ", html.unescape(title)).strip()
        results.append({"url": link, "title": title, "domain": domain})
        if len(results) >= MAX_SEARCH_RESULTS:
            break
    return results


def fetch_page(url: str) -> tuple[str, str]:
    body, ctype = _request(url)
    if "html" not in ctype.lower() and "<html" not in body[:2000].lower():
        return "", ""
    parser = TextParser()
    parser.feed(body)
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    return parser.title[:500], text[:250_000]


def requirement_terms(requirement: str) -> set[str]:
    return REQ_TERMS.get(requirement, {requirement.replace("_", " ")})


def _contains_term(text: str, terms: set[str]) -> bool:
    low = text.lower()
    return any(term in low for term in terms)


def anchor_hits(text: str, anchors: list[str]) -> list[str]:
    low = norm(text)
    return [a for a in anchors if a in low]


def evidence_excerpt(text: str, requirement: str, anchors: list[str], radius: int = 420) -> str:
    low = text.lower()
    positions = []
    for term in requirement_terms(requirement):
        i = low.find(term)
        if i >= 0:
            positions.append(i)
    for anchor in anchors:
        i = low.find(anchor)
        if i >= 0:
            positions.append(i)
    if not positions:
        return text[:900]
    center = min(positions)
    start = max(0, center - radius)
    end = min(len(text), center + radius)
    return re.sub(r"\s+", " ", text[start:end]).strip()[:1200]


def page_supports_requirement(title: str, text: str, requirement: str, anchors: list[str]) -> tuple[bool, list[str]]:
    material = f"{title} {text}"
    hits = anchor_hits(material, anchors)
    if len(set(hits)) < 2:
        return False, hits
    if not _contains_term(material, requirement_terms(requirement)):
        return False, hits
    return True, sorted(set(hits))


def research_candidate(candidate_name: str, requirements: list[str]) -> dict[str, Any]:
    path, candidate = candidate_payload(candidate_name)
    if not path or not candidate:
        raise RuntimeError(f"candidate_not_found:{candidate_name}")

    anchors = candidate_terms(candidate, candidate_name)
    if len(anchors) < 2:
        raise RuntimeError("candidate_anchor_set_too_small")

    started = time.time()
    source_rows: list[dict[str, Any]] = []
    query_log: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_urls: set[str] = set()

    for requirement in requirements:
        requirement = str(requirement).strip().lower()
        accepted_for_requirement = 0
        pages_checked = 0

        for query in build_queries(candidate, requirement):
            if accepted_for_requirement >= MAX_EVIDENCE_PER_REQUIREMENT:
                break

            try:
                results = search_duckduckgo(query)
                query_log.append({"requirement": requirement, "query": query, "results": len(results)})
            except Exception as exc:
                errors.append(f"search:{requirement}:{type(exc).__name__}:{str(exc)[:160]}")
                continue

            for result in results:
                if accepted_for_requirement >= MAX_EVIDENCE_PER_REQUIREMENT:
                    break
                if pages_checked >= MAX_PAGES_PER_REQUIREMENT:
                    break
                url = result["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                pages_checked += 1

                try:
                    page_title, page_text = fetch_page(url)
                except Exception as exc:
                    errors.append(f"fetch:{result.get('domain')}:{type(exc).__name__}:{str(exc)[:160]}")
                    continue

                ok, hits = page_supports_requirement(
                    page_title or result.get("title",""),
                    page_text,
                    requirement,
                    anchors,
                )
                if not ok:
                    continue

                summary = evidence_excerpt(page_text, requirement, anchors)
                if not summary:
                    continue

                # Important: source_rows contain only source-observed material.
                # Candidate name / requirement labels stay outside each row so
                # the evidence validator cannot pass merely from our metadata.
                source_rows.append({
                    "source": result.get("domain") or "public_web",
                    "publisher": result.get("domain") or "public_web",
                    "url": url,
                    "title": (page_title or result.get("title") or "")[:500],
                    "summary": summary,
                    "observed_at": time.time(),
                    "anchor_hits": hits,
                })
                accepted_for_requirement += 1

    artifact = {
        "schema": "companyos.targeted_public_evidence.v69_21",
        "candidate_name": candidate_name,
        "candidate_source": str(path),
        "candidate_anchors": anchors,
        "requirements_requested": requirements,
        "queries": query_log,
        "source_rows": source_rows,
        "source_row_count": len(source_rows),
        "errors": errors[-30:],
        "started_at_unix": started,
        "finished_at_unix": time.time(),
        "external_action_performed": False,
        "financial_action_performed": False,
        "deployment_performed": False,
    }

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    stamp = int(started * 1000)
    safe = re.sub(r"[^a-z0-9]+", "_", candidate_name.lower()).strip("_")[:80] or "candidate"
    out = RESEARCH_DIR / f"targeted_evidence_{safe}_{stamp}.json"
    atomic(out, artifact)

    state = {
        "schema": "companyos.targeted_public_evidence_state.v69_21",
        "last_run_unix": time.time(),
        "candidate_name": candidate_name,
        "requirements_requested": requirements,
        "source_row_count": len(source_rows),
        "artifact": str(out),
        "query_count": len(query_log),
        "error_count": len(errors),
        "healthy": True,
    }
    atomic(STATE, state)
    return {**state, "queries": query_log, "errors": errors[-10:]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--requirements", nargs="+", default=["pricing","buyer_demand"])
    args = parser.parse_args()
    print(json.dumps(research_candidate(args.candidate, args.requirements), indent=2, sort_keys=True))
