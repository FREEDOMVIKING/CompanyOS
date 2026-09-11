class ProductionScheduler:
    def schedule(self, missions):
        rows=sorted(
            missions or [],
            key=lambda x:(-int(x.get("priority",0)), x.get("created_at",""))
        )
        return [
            {**m,"slot":i+1,"status":"scheduled"}
            for i,m in enumerate(rows)
        ]
