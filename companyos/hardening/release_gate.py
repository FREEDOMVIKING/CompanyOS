class ReleaseGate:
    def evaluate(self, health, slos, config, secrets, rollback):
        checks={
            "health":bool(health.get("healthy")),
            "slos":bool(slos.get("all_met")),
            "config":bool(config.get("valid")),
            "secrets":bool(secrets.get("safe")),
            "rollback":bool(rollback.get("ready")),
        }
        return {"passed":all(checks.values()),"checks":checks}
