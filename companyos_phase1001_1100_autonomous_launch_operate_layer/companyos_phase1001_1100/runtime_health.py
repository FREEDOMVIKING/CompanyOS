class LaunchOperateHealth:
    """1099: health summary."""
    def evaluate(self,result):
        return {
            "healthy":bool((result or {}).get("success"))
                and bool(((result or {}).get("launch_health") or {}).get("healthy",True)),
            "status":(result or {}).get("status"),
            "incident_count":len(((result or {}).get("incidents") or {}).get("incidents",[])),
            "deployment_success":bool(((result or {}).get("deployment") or {}).get("success",True)),
        }
