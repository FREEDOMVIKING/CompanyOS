
import json
import os
import subprocess
import tarfile
import tempfile
import time
import urllib.request
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

def fetch_json(url, timeout=3):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        raw = r.read()
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {"status": "online"}

class CommandCenterV25:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/command_center_v25_950001_1000000"
        self.records = self.home / "command_center_records_v25"
        self.backups = self.home / "backups_v25"
        for p in (self.live, self.runtime, self.records, self.backups):
            p.mkdir(parents=True, exist_ok=True)

        self.services = [
            ("master_controls", 8766, "/", None),
            ("venture_progress", 8767, "/", None),
            ("activity_ledger", 8768, "/", None),
            ("crypto_storefront", 8772, "/api/status", None),
            ("revenue_pipeline", 8773, "/api/status", "autonomous_revenue_v11ctl"),
            ("sales_marketing", 8774, "/api/status", "autonomous_sales_marketing_v12ctl"),
            ("customer_crm", 8775, "/api/status", "customer_growth_crm_v13ctl"),
            ("commercial_operations", 8776, "/api/status", "commercial_operations_v14ctl"),
            ("enterprise_automation", 8777, "/api/status", "enterprise_automation_v15ctl"),
            ("executive_intelligence", 8778, "/api/status", "executive_intelligence_v16ctl"),
            ("autonomous_operations", 8779, "/api/status", "autonomous_operations_v17ctl"),
            ("global_dashboard", 8780, "/api/status", "global_executive_dashboard_v18ctl"),
            ("venture_launcher", 8781, "/api/status", "external_venture_launcher_v19ctl"),
            ("validation_director", 8782, "/api/status", "validation_launch_director_v20ctl"),
            ("opportunity_intelligence", 8783, "/api/status", "opportunity_intelligence_v21ctl"),
            ("research_network", 8784, "/api/status", "autonomous_research_network_v22ctl"),
            ("learning_engine", 8785, "/api/status", "self_improvement_learning_v23ctl"),
            ("specialist_workforce", 8786, "/api/status", "autonomous_specialist_workforce_v24ctl"),
        ]

    def check_services(self):
        out = []
        for name, port, path, ctl in self.services:
            started = time.time()
            try:
                payload = fetch_json(f"http://127.0.0.1:{port}{path}", timeout=3)
                out.append({
                    "name": name,
                    "port": port,
                    "alive": True,
                    "status": payload.get("status", "online"),
                    "latency_ms": round((time.time() - started) * 1000, 1),
                    "controller": ctl,
                })
            except Exception as exc:
                out.append({
                    "name": name,
                    "port": port,
                    "alive": False,
                    "status": "offline",
                    "error": str(exc),
                    "latency_ms": round((time.time() - started) * 1000, 1),
                    "controller": ctl,
                })
        return out

    def summaries(self):
        return {
            "revenue": read_json(self.live / "autonomous_revenue_v11_live.json", {}),
            "enterprise": read_json(self.live / "enterprise_automation_v15_live.json", {}),
            "validation": read_json(self.live / "validation_launch_director_v20_live.json", {}),
            "research": read_json(self.live / "autonomous_research_network_v22_live.json", {}),
            "learning": read_json(self.live / "self_improvement_learning_v23_live.json", {}),
            "workforce": read_json(self.live / "autonomous_specialist_workforce_v24_live.json", {}),
            "launcher": read_json(self.live / "external_venture_launcher_v19_live.json", {}),
            "operations": read_json(self.live / "autonomous_operations_v17_live.json", {}),
        }

    def timeline(self, limit=50):
        path = self.live / "full_autonomy_journal.jsonl"
        if not path.exists():
            return []
        rows = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        return rows[-limit:][::-1]

    def create_backup(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.backups / f"companyos_command_center_backup_{stamp}.tar.gz"
        include = [
            self.live,
            self.home / "companyos_runtime",
            self.home / "generated_ventures_v19",
            self.home / "learning_records_v23",
            self.home / "workforce_records_v24",
        ]
        with tarfile.open(dest, "w:gz") as tar:
            for p in include:
                if p.exists():
                    tar.add(p, arcname=p.relative_to(self.home))
        append_jsonl(self.records / "backup_audit.jsonl", {
            "ts": now(), "event": "backup_created", "path": str(dest)
        })
        return str(dest)

    def local_action(self, controller, action):
        allowed = {"start", "stop", "restart", "status"}
        if action not in allowed:
            return {"ok": False, "error": "unsupported_action"}
        if not controller:
            return {"ok": False, "error": "controller_not_registered"}
        path = self.home / controller
        if not path.exists():
            return {"ok": False, "error": "controller_missing", "path": str(path)}
        result = subprocess.run(
            ["bash", str(path), action],
            cwd=str(self.home),
            text=True,
            capture_output=True,
            timeout=60,
        )
        append_jsonl(self.records / "control_audit.jsonl", {
            "ts": now(),
            "controller": controller,
            "action": action,
            "returncode": result.returncode,
        })
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }

    def snapshot(self):
        services = self.check_services()
        alive = sum(1 for s in services if s["alive"])
        summaries = self.summaries()
        workforce = summaries["workforce"]
        validation = summaries["validation"]
        launcher = summaries["launcher"]
        enterprise = summaries["enterprise"]
        kpis = enterprise.get("kpis", {}) if isinstance(enterprise, dict) else {}

        state = {
            "status": "companyos_command_center_ready",
            "health_percent": round(alive / len(services) * 100) if services else 0,
            "services_alive": alive,
            "services_total": len(services),
            "services": services,
            "portfolio": {
                "ventures_prepared": launcher.get("ventures_prepared", 0),
                "ready_for_launch_review": validation.get("ready_for_launch_review", 0),
                "top_venture": launcher.get("top_venture"),
            },
            "revenue": {
                "orders_total": kpis.get("orders_total", 0),
                "paid_orders": kpis.get("paid_orders", 0),
                "revenue_usd": kpis.get("revenue_usd", 0),
                "customers": kpis.get("customers", 0),
            },
            "workforce": {
                "agents_total": workforce.get("agents_total", 0),
                "tasks_completed": workforce.get("tasks_completed", 0),
                "tasks_total": workforce.get("tasks_total", 0),
                "tasks_blocked": workforce.get("tasks_blocked", 0),
            },
            "research": {
                "network_enabled": summaries["research"].get("network_enabled", False),
                "evidence_items": summaries["research"].get("evidence_items", 0),
            },
            "learning": {
                "lessons_generated": summaries["learning"].get("lessons_generated", 0),
                "proposals": len(summaries["learning"].get("improvement_proposals", []) or []),
            },
            "timeline": self.timeline(),
            "external_actions_enabled": False,
            "automatic_code_changes_enabled": False,
            "dashboard_url": "http://127.0.0.1:8787",
            "updated_at": now(),
        }
        write_json(self.runtime / "command_center_state.json", state)
        write_json(self.live / "command_center_v25_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "command_center_v25_snapshot",
            "event_type": "command_center_v25_snapshot",
            "state": {
                "health_percent": state["health_percent"],
                "services_alive": state["services_alive"],
            },
        })
        return state
