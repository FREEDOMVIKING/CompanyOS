from pathlib import Path

class FinancialKillSwitch:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "FINANCIAL_KILL_SWITCH"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def engaged(self):
        return self.path.exists()

    def engage(self, reason="manual"):
        self.path.write_text(str(reason), encoding="utf-8")
        return {"engaged": True, "reason": str(reason)}

    def clear(self):
        if self.path.exists():
            self.path.unlink()
        return {"engaged": False}
