class RevalidationStrategyBridge:
    """916: rewrite revalidation tasks with adaptive queries/provider mix."""
    def apply(self, plan, new_query, providers, missing_sources=None):
        p=dict(plan or {})
        tasks=[]
        for item in p.get("tasks",[]):
            t=dict(item)
            inner=dict(t.get("task") or {})
            inner["query"]=f"{new_query} {inner.get('query','')}".strip()
            t["task"]=inner
            t["provider_chain"]=list(providers or [])
            t["required_missing_sources"]=list(missing_sources or [])
            tasks.append(t)
        p["tasks"]=tasks
        return p
