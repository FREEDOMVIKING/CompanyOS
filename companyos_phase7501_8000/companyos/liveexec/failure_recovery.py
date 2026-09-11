class LiveFailureRecovery:
    def plan(self, failed_executions):
        out=[]
        for x in failed_executions or []:
            kind=(x.get("result") or {}).get("error_kind","unknown")
            action={
                "provider_unavailable":"switch_provider",
                "timeout":"retry_with_backoff",
                "rate_limit":"delay_or_switch_provider",
                "network":"retry_with_backoff",
                "not_implemented":"require_real_adapter"
            }.get(kind,"diagnose")
            out.append({"job_id":x.get("job",{}).get("job_id"),"error_kind":kind,"recovery_action":action})
        return out
