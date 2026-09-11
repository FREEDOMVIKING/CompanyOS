import json
import re

class AutonomousPlanner:
    SYSTEM = """You are the planning brain for CompanyOS.
Return ONLY valid JSON. Create a practical bounded plan.
Do not claim external actions happened unless verified.
Consequential actions such as money movement, contracts, public launches,
production deploys, or external messages must be marked requires_approval=true.

Schema:
{
  "objective": "...",
  "assumptions": ["..."],
  "tasks": [
    {
      "id": "task_1",
      "department": "research|product|growth|finance|operations|customer_success",
      "kind": "research|analysis|build|growth|finance|deploy|communication",
      "instruction": "...",
      "priority": 1-10,
      "requires_approval": false,
      "success_criteria": ["..."]
    }
  ],
  "stop_conditions": ["..."]
}
"""

    def build_prompt(self, objective, context=None, memory=None):
        return [
            {"role": "system", "content": self.SYSTEM},
            {
                "role": "user",
                "content": json.dumps({
                    "objective": objective,
                    "context": context or {},
                    "recent_memory": memory or []
                }, default=str)
            }
        ]

    def parse(self, text):
        if not text:
            return {"success": False, "error": "empty_plan"}
        text = text.strip()
        try:
            return {"success": True, "plan": json.loads(text)}
        except Exception:
            pass

        # tolerate fenced JSON while still requiring a JSON object
        m = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.S)
        if m:
            try:
                return {"success": True, "plan": json.loads(m.group(1))}
            except Exception:
                pass

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return {"success": True, "plan": json.loads(text[start:end+1])}
            except Exception:
                pass
        return {"success": False, "error": "invalid_plan_json", "raw": text[:4000]}

    def validate(self, plan):
        if not isinstance(plan, dict):
            return {"passed": False, "errors": ["plan_not_object"]}
        tasks = plan.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            return {"passed": False, "errors": ["tasks_missing_or_empty"]}

        allowed_depts = {
            "research","product","growth","finance","operations","customer_success"
        }
        errors = []
        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                errors.append(f"task_{i}_not_object")
                continue
            if task.get("department") not in allowed_depts:
                errors.append(f"task_{i}_invalid_department")
            if not task.get("instruction"):
                errors.append(f"task_{i}_missing_instruction")
        return {"passed": not errors, "errors": errors}
