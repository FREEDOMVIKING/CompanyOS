class RunwayManager:
    def compute(self, cash, monthly_burn):
        cash=float(cash); burn=max(0,float(monthly_burn))
        runway=999 if burn<=0 else cash/burn
        status="healthy" if runway>=12 else ("watch" if runway>=6 else "critical")
        return {"runway_months":round(runway,2),"status":status}
