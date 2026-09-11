class ConfigDriftDetector:
    def detect(self, baseline, current):
        drift={}
        keys=set((baseline or {}))|set((current or {}))
        for k in keys:
            if (baseline or {}).get(k)!=(current or {}).get(k):
                drift[k]={"baseline":(baseline or {}).get(k),"current":(current or {}).get(k)}
        return {"drifted":bool(drift),"changes":drift}
