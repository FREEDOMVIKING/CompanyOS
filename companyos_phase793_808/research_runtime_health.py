class ResearchRuntimeHealth:
    """805: assess integrated research runtime health."""

    def evaluate(self, result):
        research = dict((result or {}).get("research_result") or {})
        execution = research.get("execution") or []
        hard_failures = [
            e for e in execution
            if not e.get("success") and e.get("error_kind") not in ("rate_limited","timeout","not_configured")
        ]
        return {
            "healthy": bool((result or {}).get("success")) and not hard_failures,
            "hard_failure_count": len(hard_failures),
            "provider_attempts": len(execution),
            "action": (result or {}).get("action"),
        }
