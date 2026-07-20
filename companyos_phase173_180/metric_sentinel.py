class MetricSentinel:
    """178: detect meaningful metric drift and trigger autonomous investigation."""
    def inspect(self, metrics):
        alerts=[]
        for m in metrics:
            value=float(m.get("value",0));baseline=float(m.get("baseline",0));tol=max(0,float(m.get("tolerance",.1)))
            denom=max(abs(baseline),1e-9);drift=(value-baseline)/denom
            if abs(drift)>tol:
                alerts.append({**m,"drift":round(drift,4),"action":"investigate_and_diagnose","autonomous":True})
        return alerts
