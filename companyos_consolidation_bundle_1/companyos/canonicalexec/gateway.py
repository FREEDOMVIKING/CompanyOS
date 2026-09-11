from pathlib import Path
import json, os
from .contracts import ExecutionRequest, ExecutionResult

class CanonicalExecutionGateway:
    def __init__(self, companyos_root=None):
        self.root = Path(companyos_root or os.environ.get("COMPANYOS_ROOT", str(Path.home()/ "companyos")))
        self.runtime = self.root / "companyos_runtime" / "canonical_execution"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.audit = self.runtime / "audit.jsonl"
        self.ids = self.runtime / "idempotency.json"

    def _launch_state(self):
        for p in [
            self.root/"companyos_runtime"/"launch_controller_state.json",
            self.root/"companyos_runtime"/"launch_controller_status.json",
        ]:
            if p.exists():
                try: return json.loads(p.read_text())
                except Exception: pass
        return {}

    def status(self):
        s = self._launch_state()
        return {
            "ready": True,
            "mode": "controlled",
            "broadcast_allowed": bool(s.get("transaction_broadcasts_allowed_by_practice_controller", False)),
            "external_actions_allowed": bool(s.get("external_actions_allowed", False) or s.get("external_action_execution", False)),
            "reason": "canonical_gateway_ready",
        }

    def _seen(self, key):
        if not self.ids.exists(): return False
        try: return key in json.loads(self.ids.read_text())
        except Exception: return False

    def _remember(self, key, result):
        try: data = json.loads(self.ids.read_text()) if self.ids.exists() else {}
        except Exception: data = {}
        data[key] = result
        self.ids.write_text(json.dumps(data, indent=2, sort_keys=True))

    def _audit(self, event, data):
        with self.audit.open("a") as f:
            f.write(json.dumps({"event":event,"data":data}, sort_keys=True)+"\n")

    def execute(self, request: ExecutionRequest):
        key = request.idempotency_key
        if self._seen(key):
            return ExecutionResult(False,"duplicate_rejected","blocked",key,"Duplicate idempotency key.")
        st = self.status()
        if request.requires_human_approval:
            r = ExecutionResult(False,"approval_required","approval_gate",key,"Human approval required.")
        elif request.external_action and not st["external_actions_allowed"]:
            r = ExecutionResult(False,"external_action_blocked","policy_gate",key,"External actions disabled.")
        elif request.financial_action and not st["broadcast_allowed"]:
            r = ExecutionResult(True,"financial_action_dry_run","dry_run",key,"Evaluated without broadcast.",
                {"action":request.action,"external_action_performed":False,"transaction_broadcast_performed":False})
        else:
            r = ExecutionResult(True,"completed_internal","internal",key,"Completed through canonical internal path.",
                {"action":request.action,"external_action_performed":False,"transaction_broadcast_performed":False})
        self._remember(key, r.to_dict())
        self._audit("execution_result", r.to_dict())
        return r
