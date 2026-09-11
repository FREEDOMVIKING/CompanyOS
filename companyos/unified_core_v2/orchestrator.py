import threading, time
from .util import stable_id, now

class Orchestrator:
    def __init__(self, core, interval=15):
        self.core = core
        self.interval = interval
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="companyos-unified-orchestrator", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.wait(self.interval):
            try:
                self.core.run_cycle()
            except Exception as e:
                self.core.db.event("orchestrator.error", "orchestrator", {"error":str(e),"ts":now()})

    def create_tasks(self):
        ventures = self.core.db.list_ventures()
        modules = self.core.db.list_modules()

        self.core.db.add_task(
            stable_id("task","system_health",len(modules)),
            "system_health",
            "Refresh unified system health",
            90,
            "recovery",
            {"module_count":len(modules)}
        )

        self.core.db.add_task(
            stable_id("task","portfolio_review",len(ventures)),
            "portfolio_review",
            "Refresh venture portfolio priorities",
            80,
            "ceo",
            {"venture_count":len(ventures)}
        )

        for v in ventures[:5]:
            if float(v.get("score",0) or 0) >= 70:
                self.core.db.add_task(
                    stable_id("task","launch",v["venture_id"],v.get("stage")),
                    "launch_readiness",
                    f"Review launch readiness: {v['name']}",
                    75,
                    "launch",
                    {"venture_id":v["venture_id"],"venture_name":v["name"],"stage":v.get("stage"),"score":v.get("score")}
                )

    def execute_tasks(self, limit=8):
        processed = 0
        for task in self.core.db.next_tasks(limit):
            self.core.db.update_task(task["task_id"], "RUNNING", 1)
            try:
                self.core.agent_runner.run(task)
                self.core.db.update_task(task["task_id"], "COMPLETED")
            except Exception:
                self.core.db.update_task(task["task_id"], "FAILED")
            processed += 1
        return processed
