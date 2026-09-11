from pathlib import Path
from .util import read_json, stable_id, now

class LegacyMigrator:
    def __init__(self, home, db):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.db = db

    def _status_value(self, payload):
        for key in ("status","state","health"):
            if key in payload:
                return str(payload.get(key))
        return "unknown"

    def _healthy(self, status):
        s = str(status).lower()
        bad = ("fail","error","stopped","down","unhealthy")
        return not any(x in s for x in bad)

    def scan_live_json(self):
        found = 0
        if not self.live.exists():
            return found
        for p in sorted(self.live.glob("*.json")):
            payload = read_json(p, {})
            if not isinstance(payload, dict):
                continue
            module_id = stable_id("legacy-module", p.name)
            status = self._status_value(payload)
            self.db.upsert_module(
                module_id=module_id,
                name=p.stem,
                source=str(p),
                status=status,
                healthy=self._healthy(status),
                payload=payload
            )
            found += 1
        return found

    def extract_ventures(self):
        count = 0
        candidates = [
            self.live / "portfolio_orchestrator_v34_live.json",
            self.live / "autonomous_venture_incubator_v35_live.json",
            self.live / "autonomous_launch_director_v36_live.json",
            self.live / "autonomous_launch_control_v37_live.json",
        ]
        seen = set()
        for path in candidates:
            d = read_json(path, {})
            items = []
            items += d.get("ventures", []) or []
            items += d.get("candidates", []) or []
            items += d.get("reviews", []) or []
            items += d.get("approved_for_launch_prep", []) or []
            for v in items:
                name = v.get("name") or v.get("venture_name")
                if not name:
                    continue
                vid = v.get("venture_id") or stable_id("venture", name, length=16)
                if vid in seen:
                    continue
                seen.add(vid)
                stage = (
                    v.get("launch_state")
                    or v.get("incubator_stage")
                    or v.get("recommended_action")
                    or v.get("effective_status")
                    or v.get("status")
                    or "UNKNOWN"
                )
                score = (
                    v.get("launch_score")
                    or v.get("portfolio_score")
                    or v.get("overall_score")
                    or v.get("score")
                    or 0
                )
                self.db.upsert_venture(vid, name, stage, score, str(path), v)
                count += 1
        return count

    def run(self):
        modules = self.scan_live_json()
        ventures = self.extract_ventures()
        report = {
            "status":"migration_scan_complete",
            "modules_discovered":modules,
            "ventures_discovered":ventures,
            "updated_at":now()
        }
        self.db.set_kv("migration_report", report)
        self.db.event("migration.scan", "legacy_migrator", report)
        return report
