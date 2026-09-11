class ProviderInvoker:
    def invoke(self, connector, job, simulate=True):
        if not connector:
            return {"success":False,"error_kind":"provider_unavailable","error":"no_connector"}
        if simulate:
            return {
                "success":True,
                "provider":connector.get("name"),
                "job_id":job.get("job_id"),
                "action":job.get("action"),
                "result":{"simulated":True,"echo":job.get("payload",{})}
            }
        return {
            "success":False,
            "provider":connector.get("name"),
            "job_id":job.get("job_id"),
            "error_kind":"not_implemented",
            "error":"real provider invocation adapter required"
        }
