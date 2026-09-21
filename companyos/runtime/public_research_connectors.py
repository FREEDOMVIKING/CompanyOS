from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os
import time
import urllib.parse
import urllib.request

STATE_ROOT = Path.home() / ".companyos_runtime" / "external_research_network"
STATE_ROOT.mkdir(parents=True, exist_ok=True)
ROTATION_FILE = STATE_ROOT / "topic_rotation.json"

TOPICS = [
    "small business automation",
    "AI workflow software",
    "SaaS pain point",
    "business operations problem",
    "developer productivity",
    "data API business",
    "marketplace software",
    "customer service automation",
    "compliance software",
    "digital product business",
    "lead generation software",
    "local service software",
]

TIMEOUT = int(os.getenv("COMPANYOS_RESEARCH_HTTP_TIMEOUT_SECONDS", "10"))
PER_SOURCE = int(os.getenv("COMPANYOS_RESEARCH_RESULTS_PER_SOURCE", "3"))

@dataclass
class ConnectorResult:
    source: str
    title: str
    summary: str
    url: str
    metadata: dict[str, Any]
    captured_at: float

def _get_json(url: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CompanyOS-Research/1.2",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read(1_250_000).decode("utf-8", "replace"))

def _next_topic() -> str:
    idx = 0
    try:
        d = json.loads(ROTATION_FILE.read_text())
        idx = int(d.get("index", 0))
    except Exception:
        pass

    topic = TOPICS[idx % len(TOPICS)]
    nxt = {"index": (idx + 1) % len(TOPICS), "last_topic": topic, "updated_at": time.time()}
    tmp = ROTATION_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(nxt, indent=2) + "\n")
    os.replace(tmp, ROTATION_FILE)
    return topic

def _hn(topic: str) -> list[ConnectorResult]:
    q = urllib.parse.quote(topic)
    url = f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage={PER_SOURCE}"
    data = _get_json(url)
    out = []
    for row in (data.get("hits") or [])[:PER_SOURCE]:
        title = row.get("title") or row.get("story_title") or ""
        link = row.get("url") or row.get("story_url") or (
            f"https://news.ycombinator.com/item?id={row.get('objectID')}" if row.get("objectID") else ""
        )
        out.append(ConnectorResult(
            source="hackernews",
            title=title,
            summary=f"Hacker News signal for topic '{topic}'. Points={row.get('points')}, comments={row.get('num_comments')}.",
            url=link,
            metadata={"topic": topic, "points": row.get("points"), "comments": row.get("num_comments")},
            captured_at=time.time(),
        ))
    return out

def _github(topic: str) -> list[ConnectorResult]:
    q = urllib.parse.quote(topic)
    url = f"https://api.github.com/search/repositories?q={q}&sort=updated&order=desc&per_page={PER_SOURCE}"
    data = _get_json(url)
    out = []
    for row in (data.get("items") or [])[:PER_SOURCE]:
        out.append(ConnectorResult(
            source="github",
            title=row.get("full_name") or row.get("name") or "",
            summary=row.get("description") or f"GitHub repository signal for '{topic}'.",
            url=row.get("html_url") or "",
            metadata={
                "topic": topic,
                "stars": row.get("stargazers_count"),
                "forks": row.get("forks_count"),
                "language": row.get("language"),
                "updated_at": row.get("updated_at"),
            },
            captured_at=time.time(),
        ))
    return out

def _stackexchange(topic: str) -> list[ConnectorResult]:
    q = urllib.parse.quote(topic)
    url = (
        "https://api.stackexchange.com/2.3/search/advanced"
        f"?order=desc&sort=activity&q={q}&site=stackoverflow&pagesize={PER_SOURCE}"
    )
    data = _get_json(url)
    out = []
    for row in (data.get("items") or [])[:PER_SOURCE]:
        out.append(ConnectorResult(
            source="stackexchange",
            title=row.get("title") or "",
            summary=f"Active developer/customer pain-point signal for '{topic}'. Tags: {', '.join(row.get('tags') or [])}.",
            url=row.get("link") or "",
            metadata={
                "topic": topic,
                "score": row.get("score"),
                "answers": row.get("answer_count"),
                "views": row.get("view_count"),
                "tags": row.get("tags") or [],
            },
            captured_at=time.time(),
        ))
    return out

# COMPANYOS_V69_31_GDELT_WIKIPEDIA_CONNECTORS
def _gdelt(topic: str) -> list[ConnectorResult]:
    params = urllib.parse.urlencode({
        "query": topic,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max(1, min(10, PER_SOURCE)),
        "sort": "HybridRel",
    })
    data = _get_json("https://api.gdeltproject.org/api/v2/doc/doc?" + params)
    rows = data.get("articles") or data.get("results") or []
    out = []
    for row in rows[:PER_SOURCE]:
        if not isinstance(row, dict):
            continue
        out.append(ConnectorResult(
            source="gdelt",
            title=row.get("title") or "",
            summary=(
                f"Recent news signal for '{topic}'. "
                f"Domain={row.get('domain')}, country={row.get('sourcecountry')}."
            ),
            url=row.get("url") or "",
            metadata={
                "topic": topic,
                "domain": row.get("domain"),
                "seen_date": row.get("seendate"),
                "language": row.get("language"),
                "source_country": row.get("sourcecountry"),
            },
            captured_at=time.time(),
        ))
    return out

def _wikipedia(topic: str) -> list[ConnectorResult]:
    q = urllib.parse.urlencode({
        "q": topic,
        "limit": max(1, min(10, PER_SOURCE)),
    })
    data = _get_json("https://en.wikipedia.org/w/rest.php/v1/search/page?" + q)
    out = []
    for row in (data.get("pages") or [])[:PER_SOURCE]:
        if not isinstance(row, dict):
            continue
        title = row.get("title") or ""
        key = row.get("key") or str(title).replace(" ", "_")
        out.append(ConnectorResult(
            source="wikipedia",
            title=title,
            summary=" ".join(
                x for x in (
                    str(row.get("description") or "").strip(),
                    str(row.get("excerpt") or "").strip(),
                ) if x
            ),
            url="https://en.wikipedia.org/wiki/" + urllib.parse.quote(str(key), safe="()_-'"),
            metadata={
                "topic": topic,
                "matched_title": row.get("matched_title"),
            },
            captured_at=time.time(),
        ))
    return out

def collect_public_research() -> tuple[str, list[dict[str, Any]], list[str]]:
    topic = _next_topic()
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for name, fn in (
        ("hackernews", _hn),
        ("github", _github),
        ("stackexchange", _stackexchange),
        ("gdelt", _gdelt),
        ("wikipedia", _wikipedia),
    ):
        try:
            for item in fn(topic):
                rows.append({
                    "source": item.source,
                    "title": item.title,
                    "summary": item.summary,
                    "url": item.url,
                    "metadata": item.metadata,
                    "captured_at": item.captured_at,
                })
        except Exception as exc:
            errors.append(f"{name}:{type(exc).__name__}:{str(exc)[:180]}")

    return topic, rows, errors
