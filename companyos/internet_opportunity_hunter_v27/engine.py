
import hashlib
import json
import os
import re
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def append_jsonl(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

def clean(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or ""))).strip()

def slug(value):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(value).lower())).strip("-")

STOP = {
    "this","that","with","from","your","have","will","into","over","more","than","when",
    "business","company","market","product","service","services","solution","solutions",
    "digital","using","their","about","after","before","between","through","online"
}

class InternetOpportunityHunterV27:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/internet_opportunity_hunter_v27_1050001_1100000"
        self.records = self.home / "opportunity_hunter_records_v27"
        self.config = self.live / "opportunity_sources_v27.json"
        self.manual = self.live / "manual_opportunity_signals_v27.json"
        self.queue_file = self.live / "approved_opportunities.json"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)
        self.ensure_config()

    def ensure_config(self):
        if not self.config.exists():
            write_json(self.config, {
                "network_enabled": False,
                "timeout_seconds": 6,
                "max_items_per_source": 30,
                "minimum_confidence": 60,
                "sources": [{
                    "source_id": "local_manual_signals",
                    "name": "Local Manual Opportunity Signals",
                    "type": "local_json",
                    "enabled": True,
                    "path": str(self.manual),
                }]
            })
        if not self.manual.exists():
            write_json(self.manual, {"items": []})

    def fetch(self, source, timeout, limit):
        stype = source.get("type")
        if stype == "local_json":
            data = read_json(source.get("path", ""), {"items": []})
            return list(data.get("items", []))[:limit]

        if stype == "json":
            req = urllib.request.Request(
                source.get("url", ""),
                headers={"User-Agent": "CompanyOS-Opportunity-Hunter-V27/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, list):
                return data[:limit]
            return list(data.get(source.get("items_key", "items"), []))[:limit]

        if stype in ("rss", "atom"):
            req = urllib.request.Request(
                source.get("url", ""),
                headers={"User-Agent": "CompanyOS-Opportunity-Hunter-V27/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                root = ET.fromstring(r.read())
            items = []
            for node in root.findall(".//item")[:limit]:
                items.append({
                    "title": clean(node.findtext("title")),
                    "summary": clean(node.findtext("description")),
                    "url": clean(node.findtext("link")),
                    "published_at": clean(node.findtext("pubDate")),
                })
            if not items:
                ns = {"a": "http://www.w3.org/2005/Atom"}
                for node in root.findall(".//a:entry", ns)[:limit]:
                    link = node.find("a:link", ns)
                    items.append({
                        "title": clean(node.findtext("a:title", default="", namespaces=ns)),
                        "summary": clean(node.findtext("a:summary", default="", namespaces=ns)),
                        "url": link.get("href") if link is not None else "",
                        "published_at": clean(node.findtext("a:updated", default="", namespaces=ns)),
                    })
            return items
        raise ValueError(f"unsupported_source_type:{stype}")

    def normalize(self, source, item):
        title = clean(item.get("title") or item.get("name"))
        summary = clean(item.get("summary") or item.get("description") or item.get("text"))
        text = f"{title} {summary}".strip()
        return {
            "signal_id": hashlib.sha256(
                f"{source.get('source_id')}|{title}|{item.get('url')}".encode()
            ).hexdigest()[:20],
            "source_id": source.get("source_id"),
            "source_name": source.get("name"),
            "title": title,
            "summary": summary,
            "url": item.get("url") or item.get("link"),
            "published_at": item.get("published_at") or item.get("date"),
            "signal_type": item.get("signal_type") or "opportunity_signal",
            "competitor": item.get("competitor"),
            "supplier": item.get("supplier"),
            "lead_source": item.get("lead_source"),
            "estimated_price_usd": item.get("estimated_price_usd"),
            "keywords": self.keywords(text),
        }

    def keywords(self, text):
        words = re.findall(r"[a-z0-9]+", text.lower())
        return [w for w in words if len(w) >= 4 and w not in STOP]

    def candidates(self, signals, min_confidence):
        keyword_counts = Counter()
        for s in signals:
            keyword_counts.update(set(s["keywords"]))

        candidates = []
        for s in signals:
            hits = sum(keyword_counts[k] for k in set(s["keywords"]))
            specificity = min(20, len(set(s["keywords"])) * 2)
            source_strength = 20 if s.get("url") else 10
            commercial = 0
            text = f"{s['title']} {s['summary']}".lower()
            for term in ("buy", "price", "cost", "demand", "customer", "lead", "supplier", "software", "template"):
                if term in text:
                    commercial += 4
            metadata = 0
            metadata += 5 if s.get("competitor") else 0
            metadata += 5 if s.get("supplier") else 0
            metadata += 5 if s.get("lead_source") else 0
            metadata += 5 if isinstance(s.get("estimated_price_usd"), (int, float)) else 0

            confidence = min(100, 25 + min(25, hits) + specificity + min(20, commercial) + metadata)
            if confidence < min_confidence:
                continue

            name = s["title"] or "Discovered Opportunity"
            opportunity_id = slug(name)[:70] or s["signal_id"]
            candidates.append({
                "opportunity_id": opportunity_id,
                "name": name,
                "status": "DISCOVERED_REVIEW_REQUIRED",
                "score": confidence,
                "summary": s["summary"],
                "source_signal_id": s["signal_id"],
                "source_id": s["source_id"],
                "source_url": s.get("url"),
                "keywords": s["keywords"][:15],
                "competitor": s.get("competitor"),
                "supplier": s.get("supplier"),
                "lead_source": s.get("lead_source"),
                "estimated_price_usd": s.get("estimated_price_usd"),
                "external_build_approved": False,
                "external_launch_approved": False,
                "discovered_at": now(),
            })

        dedup = {}
        for c in candidates:
            old = dedup.get(c["opportunity_id"])
            if not old or c["score"] > old["score"]:
                dedup[c["opportunity_id"]] = c
        return sorted(dedup.values(), key=lambda x: x["score"], reverse=True)

    def run_cycle(self):
        config = read_json(self.config, {})
        network_enabled = bool(config.get("network_enabled", False))
        timeout = int(config.get("timeout_seconds", 6) or 6)
        limit = int(config.get("max_items_per_source", 30) or 30)
        min_confidence = int(config.get("minimum_confidence", 60) or 60)

        signals = []
        source_status = []
        for source in config.get("sources", []):
            if not source.get("enabled"):
                source_status.append({"source_id": source.get("source_id"), "status": "DISABLED", "items": 0})
                continue
            if source.get("type") != "local_json" and not network_enabled:
                source_status.append({"source_id": source.get("source_id"), "status": "NETWORK_DISABLED", "items": 0})
                continue
            try:
                raw = self.fetch(source, timeout, limit)
                normalized = [self.normalize(source, item) for item in raw]
                signals.extend(normalized)
                source_status.append({"source_id": source.get("source_id"), "status": "OK", "items": len(normalized)})
            except Exception as exc:
                source_status.append({
                    "source_id": source.get("source_id"),
                    "status": "ERROR",
                    "items": 0,
                    "error": str(exc),
                })

        opportunities = self.candidates(signals, min_confidence)
        queue = {
            "opportunities": opportunities,
            "updated_at": now(),
            "source": "internet_opportunity_hunter_v27",
        }
        write_json(self.queue_file, queue)

        state = {
            "status": "internet_opportunity_hunter_ready",
            "network_enabled": network_enabled,
            "sources_total": len(config.get("sources", [])),
            "sources_ok": sum(s["status"] == "OK" for s in source_status),
            "signals_collected": len(signals),
            "opportunities_discovered": len(opportunities),
            "top_opportunity": opportunities[0]["name"] if opportunities else None,
            "source_status": source_status,
            "opportunities": opportunities,
            "external_actions_enabled": False,
            "automatic_build_enabled": False,
            "dashboard_url": "http://127.0.0.1:8789",
            "updated_at": now(),
        }

        write_json(self.runtime / "opportunity_hunter_state.json", state)
        write_json(self.live / "internet_opportunity_hunter_v27_live.json", state)
        write_json(self.records / "discovery_queue.json", queue)
        append_jsonl(self.records / "discovery_audit.jsonl", {
            "ts": now(),
            "event": "discovery_cycle",
            "signals_collected": len(signals),
            "opportunities_discovered": len(opportunities),
            "network_enabled": network_enabled,
        })
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "internet_opportunity_hunter_v27_cycle",
            "event_type": "internet_opportunity_hunter_v27_cycle",
            "state": {
                "signals_collected": len(signals),
                "opportunities_discovered": len(opportunities),
                "top_opportunity": state["top_opportunity"],
            },
        })
        return state
