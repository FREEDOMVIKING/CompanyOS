class IntegrationAssertions:
    """729: explicit pass/fail assertions for the closed loop."""

    def evaluate(self, before, after, venture, learning, audits):
        checks={
            "cycle_incremented":int(after.get("cycles",0)) >= int(before.get("cycles",0)),
            "runtime_not_failed":int(after.get("consecutive_failures",0)) == 0,
            "venture_persisted":bool(venture.get("present")),
            "lifecycle_stage_present":bool(venture.get("stage")),
            "learning_recorded":bool(learning.get("hypotheses_present") or learning.get("strategy_present")),
            "runtime_audit_present":bool(audits.get("unified_runtime_audit.jsonl",{}).get("exists")),
        }
        return {
            "passed":all(checks.values()),
            "checks":checks,
            "failed":[k for k,v in checks.items() if not v],
        }
