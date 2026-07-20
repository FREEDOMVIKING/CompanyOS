class ForecastEngine:
    """110: simple scenario forecast with confidence bounds."""
    def forecast(self,history,growth_rate=0.0,periods=3,uncertainty=.15):
        base=float(history[-1]) if history else 0.0;out=[]
        for i in range(1,max(1,int(periods))+1):
            expected=base*((1+float(growth_rate))**i);u=abs(float(uncertainty))
            out.append({"period":i,"low":round(expected*(1-u),2),"expected":round(expected,2),"high":round(expected*(1+u),2)})
        return out
