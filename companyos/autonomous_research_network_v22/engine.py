
import json
import os
import re
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
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

def clean_text(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or ""))).strip()

def keywordize(name):
    words = re.findall(r"[a-z0-9]+", str(name).lower())
    stop = {"business", "company", "venture", "digital", "the", "and", "for"}
    return [w for w in words if w not in stop and len(w) >= 3]

class AutonomousResearchNetworkV22:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_research_network_v22_800001_850000"
        self.records = self.home / "research_records_v22"
        self.ventures = self.home / "generated_ventures_v19"
        self.config = self.live / "research_sources_v22.json"
        self.shared_evidence = self.live / "external_research_evidence_v22.json"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)
        self.ensure_default_config()

    def ensure_default_config(self):
        if self.config.exists():
            return
        write_json(self.config, {
            "network_enabled": False,
            "timeout_seconds": 5,
            "max_items_per_source": 25,
            "sources": [
                {
                    "source_id": "local_manual_evidence",
                    "name": "Local Manual Evidence",
                    "type": "local_json",
                    "enabled": True,
                    "path": str(self.live / "manual_research_evidence.json"),
                }
            ]
        })
        manual = self.live / "manual_research_evidence.json"
        if not manual.exists():
            write_json(manual, {"items": []})

    def active_ventures(self):
        items = []
        if self.ventures.exists():
            for p in sorted(self.ventures.iterdir()):
                if not p.is_dir():
                    continue
                manifest = read_json(p / "venture_manifest.json", {})
                items.append({
                    "venture_id": manifest.get("venture_id", p.name),
                    "name": manifest.get("name", p.name),
                    "keywords": keywordize(manifest.get("name", p.name)),
                    "workspace": str(p),
                })
        return items

    def fetch_source(self, source, timeout, max_items):
        stype = source.get("type")
        if stype == "local_json":
            data = read_json(source.get("path", ""), {"items": []})
            return list(data.get("items", []))[:max_items]

        if stype == "json":
            req = urllib.request.Request(
                source.get("url", ""),
                headers={"User-Agent": "CompanyOS-Research-V22/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, list):
                return data[:max_items]
            return list(data.get(source.get("items_key", "items"), []))[:max_items]

        if stype in ("rss", "atom"):
            req = urllib.request.Request(
                source.get("url", ""),
                headers={"User-Agent": "CompanyOS-Research-V22/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            root = ET.fromstring(raw)
            results = []
            for node in root.findall(".//item")[:max_items]:
                results.append({
                    "title": clean_text(node.findtext("title")),
                    "summary": clean_text(node.findtext("description")),
                    "url": clean_text(node.findtext("link")),
                    "published_at": clean_text(node.findtext("pubDate")),
                })
            if not results:
                ns = {"a": "http://www.w3.org/2005/Atom"}
                for node in root.findall(".//a:entry", ns)[:max_items]:
                    link = node.find("a:link", ns)
                    results.append({
                        "title": clean_text(node.findtext("a:title", default="", namespaces=ns)),
                        "summary": clean_text(node.findtext("a:summary", default="", namespaces=ns)),
                        "url": link.get("href") if link is not None else "",
                        "published_at": clean_text(node.findtext("a:updated", default="", namespaces=ns)),
                    })
            return results

        raise ValueError(f"unsupported_source_type:{stype}")

    def normalize_item(self, source, item):
        return {
            "source_id": source.get("source_id"),
            "source_name": source.get("name"),
            "title": clean_text(item.get("title") or item.get("name")),
            "summary": clean_text(item.get("summary") or item.get("description") or item.get("text")),
            "url": item.get("url") or item.get("link"),
            "published_at": item.get("published_at") or item.get("date"),
            "price_usd": item.get("price_usd"),
            "competitor": item.get("competitor"),
            "signal_type": item.get("signal_type") or "market_signal",
        }

    def match_evidence(self, ventures, evidence):
        results = {}
        for venture in ventures:
            keywords = venture.get("keywords", [])
            matched = []
            for item in evidence:
                haystack = f"{item.get('title','')} {item.get('summary','')}".lower()
                hits = [k for k in keywords if k in haystack]
                if hits:
                    matched.append({**item, "matched_keywords": hits})
            competitors = sorted({
                str(x.get("competitor")) for x in matched if x.get("competitor")
            })
            prices = [
                float(x.get("price_usd")) for x in matched
                if isinstance(x.get("price_usd"), (int, float))
            ]
            signal_score = min(100, len(matched) * 12 + len(competitors) * 5 + min(len(prices), 5) * 4)
            results[venture["venture_id"]] = {
                "venture_id": venture["venture_id"],
                "name": venture["name"],
                "matched_items": len(matched),
                "competitors": competitors,
                "observed_prices_usd": prices,
                "external_signal_score": signal_score,
                "evidence": matched[:50],
                "updated_at": now(),
            }
        return results

    def run_cycle(self):
        config = read_json(self.config, {})
        ventures = self.active_ventures()
        network_enabled = bool(config.get("network_enabled", False))
        timeout = int(config.get("timeout_seconds", 5) or 5)
        max_items = int(config.get("max_items_per_source", 25) or 25)

        evidence = []
        source_status = []
        for source in config.get("sources", []):
            if not source.get("enabled"):
                source_status.append({
                    "source_id": source.get("source_id"),
                    "status": "DISABLED",
                    "items": 0,
                })
                continue
            if source.get("type") != "local_json" and not network_enabled:
                source_status.append({
                    "source_id": source.get("source_id"),
                    "status": "NETWORK_DISABLED",
                    "items": 0,
                })
                continue
            try:
                items = self.fetch_source(source, timeout, max_items)
                normalized = [self.normalize_item(source, i) for i in items]
                evidence.extend(normalized)
                source_status.append({
                    "source_id": source.get("source_id"),
                    "status": "OK",
                    "items": len(normalized),
                })
            except Exception as exc:
                source_status.append({
                    "source_id": source.get("source_id"),
                    "status": "ERROR",
                    "items": 0,
                    "error": str(exc),
                })

        matched = self.match_evidence(ventures, evidence)
        state = {
            "status": "autonomous_research_network_ready",
            "network_enabled": network_enabled,
            "sources_total": len(config.get("sources", [])),
            "sources_ok": sum(s["status"] == "OK" for s in source_status),
            "evidence_items": len(evidence),
            "ventures_analyzed": len(ventures),
            "source_status": source_status,
            "venture_evidence": matched,
            "dashboard_url": "http://127.0.0.1:8784",
            "updated_at": now(),
        }

        write_json(self.shared_evidence, state)
        write_json(self.runtime / "research_state.json", state)
        write_json(self.live / "autonomous_research_network_v22_live.json", state)
        append_jsonl(self.records / "research_audit.jsonl", {
            "ts": now(),
            "event": "research_cycle",
            "network_enabled": network_enabled,
            "evidence_items": len(evidence),
            "sources_ok": state["sources_ok"],
        })
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_research_network_v22_cycle",
            "event_type": "autonomous_research_network_v22_cycle",
            "state": state,
        })
        return state
