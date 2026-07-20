class CashflowPlanner:
    """121: forward cash-flow planning only; never moves funds."""
    def project(self,starting_cash,monthly_inflows,monthly_outflows):
        cash=float(starting_cash);rows=[]
        n=max(len(monthly_inflows),len(monthly_outflows))
        for i in range(n):
            inc=float(monthly_inflows[i]) if i<len(monthly_inflows) else 0
            out=float(monthly_outflows[i]) if i<len(monthly_outflows) else 0
            cash+=inc-out;rows.append({"month":i+1,"inflow":inc,"outflow":out,"ending_cash":round(cash,2)})
        return {"projection":rows,"ending_cash":round(cash,2),"funds_moved":False}
