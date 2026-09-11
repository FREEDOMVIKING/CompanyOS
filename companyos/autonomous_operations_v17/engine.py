import json, os, subprocess, tempfile, time, urllib.request
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
        return json.loads(r.read().decode("utf-8"))

class AutonomousOperationsV17:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_operations_v17_550001_600000"
        self.records = self.home / "operations_records_v17"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

        self.services = {
            "storefront": {
                "url": "http://127.0.0.1:8772/api/status",
                "controller": None,
                "critical": True,
            },
            "revenue": {
                "url": "http://127.0.0.1:8773/api/status",
                "controller": "autonomous_revenue_v11ctl",
                "critical": True,
            },
            "marketing": {
                "url": "http://127.0.0.1:8774/api/status",
                "controller": "autonomous_sales_marketing_v12ctl",
                "critical": False,
            },
            "crm": {
                "url": "http://127.0.0.1:8775/api/status",
                "controller": "customer_growth_crm_v13ctl",
                "critical": False,
            },
            "commercial": {
                "url": "http://127.0.0.1:8776/api/status",
                "controller": "commercial_operations_v14ctl",
                "critical": False,
            },
            "enterprise": {
                "url": "http://127.0.0.1:8777/api/status",
                "controller": "enterprise_automation_v15ctl",
                "critical": False,
            },
            "executive": {
                "url": "http://127.0.0.1:8778/api/status",
                "controller": "executive_intelligence_v16ctl",
                "critical": False,
            },
        }

    def check_services(self):
        result = {}
        for name, spec in self.services.items():
            started = time.time()
            try:
                data = fetch_json(spec["url"])
                result[name] = {
                    "alive": True,
                    "status": data.get("status"),
                    "latency_ms": round((time.time() - started) * 1000, 1),
                    "critical": spec["critical"],
                    "controller": spec["controller"],
                }
            except Exception as exc:
                result[name] = {
                    "alive": False,
                    "status": "UNAVAILABLE",
                    "error": str(exc),
                    "latency_ms": round((time.time() - started) * 1000, 1),
                    "critical": spec["critical"],
                    "controller": spec["controller"],
                }
        return result

    def dependency_graph(self, services):
        deps = {
            "revenue": ["storefront"],
            "marketing": ["revenue"],
            "crm": ["storefront", "revenue"],
            "commercial": ["crm", "marketing"],
            "enterprise": ["revenue", "crm", "commercial"],
            "executive": ["revenue", "marketing", "crm", "commercial", "enterprise"],
        }
        checks = []
        for service, required in deps.items():
            missing = [x for x in required if not services.get(x, {}).get("alive")]
            checks.append({
                "service": service,
                "dependencies": required,
                "missing": missing,
                "ready": not missing,
            })
        return checks

    def scheduler(self, services):
        tasks = []
        order = ["storefront", "revenue", "marketing", "crm", "commercial", "enterprise", "executive"]
        for index, name in enumerate(order, start=1):
            state = services.get(name, {})
            tasks.append({
                "task_id": f"ops-{index:02d}-{name}",
                "service": name,
                "action": "HEALTH_CHECK" if state.get("alive") else "RECOVERY_REVIEW",
                "priority": 100 - index * 5 if state.get("critical") else 70 - index * 3,
                "status": "COMPLETED" if state.get("alive") else "QUEUED",
                "external_action": False,
            })
        tasks.sort(key=lambda x: x["priority"], reverse=True)
        return tasks

    def recovery_candidates(self, services):
        items = []
        for name, state in services.items():
            if state.get("alive"):
                continue
            controller = state.get("controller")
            items.append({
                "service": name,
                "controller": controller,
                "auto_recovery_supported": bool(controller),
                "recommended_command": (
                    f"bash {controller} restart"
                    if controller else
                    "Restart manually using its existing local service command"
                ),
                "status": "REVIEW_REQUIRED",
            })
        return items

    def resource_advice(self, services):
        alive = sum(1 for x in services.values() if x.get("alive"))
        slow = [name for name, x in services.items() if float(x.get("latency_ms", 0) or 0) > 1500]
        advice = []
        if alive >= 7:
            advice.append("All tracked services are active; avoid unnecessary full-stack restarts.")
        if slow:
            advice.append("Review slow local services: " + ", ".join(slow))
        if not advice:
            advice.append("Keep using direct controllers to minimize Termux memory spikes.")
        return advice

    def event_queue(self, services, dependencies):
        queue = []
        for dep in dependencies:
            if not dep["ready"]:
                queue.append({
                    "event_type": "dependency_blocked",
                    "service": dep["service"],
                    "missing": dep["missing"],
                    "priority": "HIGH",
                    "status": "OPEN",
                })
        for name, state in services.items():
            if not state.get("alive"):
                queue.append({
                    "event_type": "service_unavailable",
                    "service": name,
                    "priority": "HIGH" if state.get("critical") else "MEDIUM",
                    "status": "OPEN",
                })
        if not queue:
            queue.append({
                "event_type": "operations_healthy",
                "priority": "LOW",
                "status": "INFORMATIONAL",
            })
        return queue

    def run_cycle(self):
        services = self.check_services()
        dependencies = self.dependency_graph(services)
        tasks = self.scheduler(services)
        events = self.event_queue(services, dependencies)
        recovery = self.recovery_candidates(services)

        alive = sum(1 for x in services.values() if x.get("alive"))
        critical_down = sum(1 for x in services.values() if x.get("critical") and not x.get("alive"))
        health = max(0, min(100, round((alive / max(len(services), 1)) * 100 - critical_down * 10)))

        state = {
            "status": "autonomous_operations_ready",
            "operations_health_score": health,
            "services_alive": alive,
            "services_total": len(services),
            "critical_services_down": critical_down,
            "services": services,
            "dependencies": dependencies,
            "scheduled_tasks": tasks,
            "event_queue": events,
            "recovery_candidates": recovery,
            "resource_advice": self.resource_advice(services),
            "external_actions_enabled": False,
            "dashboard_url": "http://127.0.0.1:8779",
            "updated_at": now(),
        }

        write_json(self.runtime / "operations_state.json", state)
        write_json(self.live / "autonomous_operations_v17_live.json", state)
        write_json(self.records / "operations_snapshot_latest.json", state)
        append_jsonl(self.records / "operations_audit.jsonl", {
            "ts": now(),
            "event": "operations_cycle",
            "health": health,
            "services_alive": alive,
            "critical_services_down": critical_down,
        })
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_operations_v17_cycle",
            "event_type": "autonomous_operations_v17_cycle",
            "state": state,
        })
        return state
