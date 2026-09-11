class ForecastEngine:
    def __init__(self,db):
        self.db=db

    def forecast(self):
        ventures=self.db.list_ventures()
        weighted=sum(float(v.get("score",0) or 0) for v in ventures)
        readiness=sum(1 for v in ventures if "READY" in str(v.get("stage","")).upper())
        forecast={
            "model":"internal_readiness_forecast_v1",
            "ventures_considered":len(ventures),
            "readiness_count":readiness,
            "portfolio_signal":round(weighted/max(1,len(ventures)),2) if ventures else 0,
            "forecast_revenue_usd":0.0,
            "confidence":0.35 if ventures else 0.0,
            "note":"Revenue remains zero until verified external sales data is ingested."
        }
        self.db.set_kv("revenue_forecast",forecast)
        return forecast
