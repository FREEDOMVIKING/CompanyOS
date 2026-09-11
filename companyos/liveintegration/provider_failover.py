class ProviderFailover:
    def choose(self, providers, attempted=None):
        attempted=set(attempted or [])
        rows=[p for p in providers or [] if p.get("enabled",True) and p.get("name") not in attempted]
        rows=sorted(rows,key=lambda x:float(x.get("health_score",0)),reverse=True)
        return {
            "selected":rows[0]["name"] if rows else None,
            "remaining":[x["name"] for x in rows[1:]]
        }
