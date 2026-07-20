class SalesPipeline:
    """78: internal sales funnel state and forecasting."""
    STAGES=["lead","qualified","proposal","won","lost"]
    def forecast(self,deals):
        weighted=0.0; total=0.0
        probs={"lead":.1,"qualified":.35,"proposal":.65,"won":1.0,"lost":0.0}
        for d in deals:
            value=max(0,float(d.get("value",0))); stage=d.get("stage","lead")
            total+=value; weighted+=value*probs.get(stage,0)
        return {"pipeline_value":round(total,2),"weighted_forecast":round(weighted,2),"deal_count":len(deals)}
