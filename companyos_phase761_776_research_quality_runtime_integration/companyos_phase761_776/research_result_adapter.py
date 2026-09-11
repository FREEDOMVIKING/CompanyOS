class ResearchResultAdapter:
    """767: normalize live research execution results into evidence records."""
    def adapt(self,result,provider):
        rows=[]
        data=(result or {}).get("data") if isinstance(result,dict) else None
        candidates=[]
        if isinstance(data,dict):
            candidates=data.get("evidence") or data.get("records") or data.get("items") or []
        if not candidates and isinstance(result,dict):
            candidates=result.get("evidence") or []
        for i,item in enumerate(candidates or []):
            if isinstance(item,str):
                item={"text":item}
            row=dict(item)
            row.setdefault("id",f"{provider}_{i}")
            row.setdefault("source_class",provider)
            rows.append(row)
        return rows
