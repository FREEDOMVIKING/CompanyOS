class ResilienceScore:
    def calculate(self, signals):
        keys=["backup_ready","restore_verified","redundancy_ready","integrity_ok","continuity_ready"]
        vals=[1 if signals.get(k) else 0 for k in keys]
        score=sum(vals)/len(vals)
        return {"score":round(score,3),"ready":score>=.8}
