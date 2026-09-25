class LiveFailureRecovery:
    def plan(self, failed_executions):
        out = []
        for x in failed_executions or []:
            try:
                kind = (x.get("result") or {}).get("error_kind", "unknown")
                action = {
                    "provider_unavailable": "switch_provider",
                    "timeout": "retry_with_backoff",
                    "rate_limit": "delay_or_switch_provider",
                    "network": "retry_with_backoff",
                    "not_implemented": "require_real_adapter"
                }.get(kind, "diagnose")
                out.append({"job_id": x.get("job", {}).get("job_id"), "error_kind": kind, "recovery_action": action})
            except Exception as e:
                self.log_failure(x, e)
        return out

    def log_failure(self, x, e):
        kind = (x.get("result") or {}).get("error_kind", "unknown")
        error_message = str(e)
        self.root.log.error(f"Failed to process job {x.get('job', {}).get('job_id')}: {error_message} (kind: {kind})")
