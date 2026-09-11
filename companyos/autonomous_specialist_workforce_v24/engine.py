
import json
import os
import tempfile
from collections import Counter, defaultdict
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

class AutonomousSpecialistWorkforceV24:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_specialist_workforce_v24_900001_950000"
        self.records = self.home / "workforce_records_v24"
        self.tasks_file = self.runtime / "tasks.json"
        self.messages_file = self.runtime / "message_bus.jsonl"
        self.shared_memory = self.records / "shared_memory.json"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

        self.agents = {
            "ceo": {"name": "Executive CEO Agent", "skills": ["strategy", "prioritization", "delegation"]},
            "cto": {"name": "CTO Agent", "skills": ["architecture", "runtime", "technical_review"]},
            "cfo": {"name": "CFO Agent", "skills": ["finance", "pricing", "risk"]},
            "cmo": {"name": "CMO Agent", "skills": ["marketing", "campaigns", "positioning"]},
            "coo": {"name": "COO Agent", "skills": ["operations", "dependencies", "delivery"]},
            "research": {"name": "Research Agent", "skills": ["research", "evidence", "competition"]},
            "product_builder": {"name": "Product Builder Agent", "skills": ["product", "offer", "artifacts"]},
            "customer_support": {"name": "Customer Support Agent", "skills": ["support", "customers", "responses"]},
            "sales": {"name": "Sales Agent", "skills": ["sales", "leads", "conversion"]},
            "qa": {"name": "QA/Test Agent", "skills": ["qa", "testing", "validation"]},
        }

    def load_tasks(self):
        data = read_json(self.tasks_file, {"tasks": []})
        return data.get("tasks", [])

    def save_tasks(self, tasks):
        write_json(self.tasks_file, {"tasks": tasks, "updated_at": now()})

    def seed_tasks(self):
        tasks = self.load_tasks()
        if tasks:
            return tasks

        sources = {
            "learning": read_json(self.live / "self_improvement_learning_v23_live.json", {}),
            "validation": read_json(self.live / "validation_launch_director_v20_live.json", {}),
            "research": read_json(self.live / "autonomous_research_network_v22_live.json", {}),
            "operations": read_json(self.live / "autonomous_operations_v17_live.json", {}),
            "enterprise": read_json(self.live / "enterprise_automation_v15_live.json", {}),
        }

        seeded = []
        def add(task_id, title, role, priority, payload=None, deps=None):
            seeded.append({
                "task_id": task_id,
                "title": title,
                "assigned_role": role,
                "priority": priority,
                "status": "QUEUED",
                "payload": payload or {},
                "dependencies": deps or [],
                "created_at": now(),
                "updated_at": now(),
            })

        add("v24-ceo-priority", "Review company-wide top priority", "ceo", 100, {
            "top_venture": sources["enterprise"].get("top_priority_venture")
        })
        add("v24-cfo-pricing", "Review pricing recommendation", "cfo", 92, {
            "pricing": sources["learning"].get("pricing_recommendations", [])
        })
        add("v24-research-evidence", "Review external research coverage", "research", 90, {
            "network_enabled": sources["research"].get("network_enabled", False),
            "evidence_items": sources["research"].get("evidence_items", 0),
        })
        add("v24-product-offer", "Inspect launch-ready venture offer", "product_builder", 88, {
            "validation_results": sources["validation"].get("results", [])
        }, ["v24-research-evidence"])
        add("v24-qa-validate", "Run internal venture QA review", "qa", 86, {}, ["v24-product-offer"])
        add("v24-cmo-campaign", "Prepare campaign review brief", "cmo", 82, {}, ["v24-product-offer"])
        add("v24-sales-first-sale", "Prepare first-sale conversion brief", "sales", 80, {}, ["v24-cmo-campaign"])
        add("v24-coo-runtime", "Review runtime and dependency health", "coo", 78, {
            "operations_health": sources["operations"].get("operations_health_score")
        })
        add("v24-cto-architecture", "Review module integration health", "cto", 76, {}, ["v24-coo-runtime"])
        add("v24-support-readiness", "Prepare customer support readiness brief", "customer_support", 70)

        self.save_tasks(seeded)
        return seeded

    def task_ready(self, task, task_map):
        for dep in task.get("dependencies", []):
            if task_map.get(dep, {}).get("status") != "COMPLETED":
                return False
        return True

    def execute_task(self, task):
        role = task["assigned_role"]
        output = {
            "role": role,
            "agent": self.agents[role]["name"],
            "summary": f"{self.agents[role]['name']} completed: {task['title']}",
            "recommendation_only": True,
            "external_action_performed": False,
            "completed_at": now(),
        }

        if role == "research":
            if not task.get("payload", {}).get("network_enabled"):
                output["finding"] = "External research network is disabled; use internal evidence only."
            else:
                output["finding"] = "External research network is available."
        elif role == "cfo":
            output["finding"] = "Pricing remains provisional until verified sales exist."
        elif role == "coo":
            health = task.get("payload", {}).get("operations_health")
            output["finding"] = f"Observed operations health: {health}"
        elif role == "qa":
            output["finding"] = "Internal QA completed; external launch still requires review."
        else:
            output["finding"] = "Internal review completed."

        return output

    def append_message(self, sender, recipient, task_id, message):
        append_jsonl(self.messages_file, {
            "ts": now(),
            "sender": sender,
            "recipient": recipient,
            "task_id": task_id,
            "message": message,
        })

    def run_cycle(self):
        tasks = self.seed_tasks()
        task_map = {t["task_id"]: t for t in tasks}

        completed_now = 0
        for task in sorted(tasks, key=lambda x: x["priority"], reverse=True):
            if task["status"] == "COMPLETED":
                continue
            if not self.task_ready(task, task_map):
                task["status"] = "BLOCKED"
                task["updated_at"] = now()
                continue

            task["status"] = "IN_PROGRESS"
            task["updated_at"] = now()
            self.append_message("ceo", task["assigned_role"], task["task_id"], f"Assigned: {task['title']}")
            task["result"] = self.execute_task(task)
            task["status"] = "COMPLETED"
            task["updated_at"] = now()
            self.append_message(task["assigned_role"], "ceo", task["task_id"], task["result"]["summary"])
            completed_now += 1

        self.save_tasks(tasks)

        counts = Counter(t["status"] for t in tasks)
        by_agent = defaultdict(lambda: {"assigned": 0, "completed": 0})
        for task in tasks:
            role = task["assigned_role"]
            by_agent[role]["assigned"] += 1
            if task["status"] == "COMPLETED":
                by_agent[role]["completed"] += 1

        performance = {}
        for role, stats in by_agent.items():
            assigned = stats["assigned"]
            completed = stats["completed"]
            performance[role] = {
                "agent": self.agents[role]["name"],
                "assigned": assigned,
                "completed": completed,
                "completion_rate": round(completed / assigned, 3) if assigned else 0,
            }

        memory = {
            "agents": self.agents,
            "task_counts": dict(counts),
            "performance": performance,
            "last_completed_tasks": [
                {
                    "task_id": t["task_id"],
                    "title": t["title"],
                    "agent": self.agents[t["assigned_role"]]["name"],
                    "result": t.get("result"),
                }
                for t in tasks if t["status"] == "COMPLETED"
            ][-20:],
            "updated_at": now(),
        }
        write_json(self.shared_memory, memory)

        state = {
            "status": "autonomous_specialist_workforce_ready",
            "agents_total": len(self.agents),
            "tasks_total": len(tasks),
            "tasks_completed": counts.get("COMPLETED", 0),
            "tasks_blocked": counts.get("BLOCKED", 0),
            "tasks_completed_this_cycle": completed_now,
            "agent_performance": performance,
            "tasks": tasks,
            "automatic_external_actions_enabled": False,
            "automatic_code_changes_enabled": False,
            "dashboard_url": "http://127.0.0.1:8786",
            "updated_at": now(),
        }

        write_json(self.runtime / "workforce_state.json", state)
        write_json(self.live / "autonomous_specialist_workforce_v24_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_specialist_workforce_v24_cycle",
            "event_type": "autonomous_specialist_workforce_v24_cycle",
            "state": state,
        })
        return state
