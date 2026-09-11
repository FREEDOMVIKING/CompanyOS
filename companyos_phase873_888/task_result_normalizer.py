class TaskResultNormalizer:
    """875: flatten evidence from task execution batches."""
    def normalize(self, executions):
        out=[]
        for ex in executions or []:
            for batch in ex.get("batches",[]):
                for item in batch.get("items",[]):
                    row=dict(item)
                    row.setdefault("revalidation_dimension",(ex.get("task") or {}).get("task",{}).get("dimension"))
                    out.append(row)
        return out
