class LiveWorkerRuntime:
    def execute_once(self, job, connector, invoker, verifier, simulate=True):
        result=invoker.invoke(connector,job,simulate=simulate)
        verification=verifier.verify(job,result)
        return {
            "job":job,
            "connector":connector.get("name") if connector else None,
            "result":result,
            "verification":verification,
            "status":"complete" if verification.get("verified") else "failed"
        }
