class AdaptiveResultNormalizer:
    """923: flatten adaptive strategy task results into evidence rows."""
    def normalize(self, executions):
        rows=[]
        for ex in executions or []:
            dim=(ex.get("task") or {}).get("task",{}).get("dimension")
            for batch in ex.get("batches",[]):
                for item in batch.get("items",[]):
                    row=dict(item)
                    row.setdefault("adaptive_dimension",dim)
                    rows.append(row)
        return rows
