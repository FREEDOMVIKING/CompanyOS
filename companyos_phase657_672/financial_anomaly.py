class FinancialAnomaly:
    """665: detect basic financial anomalies."""

    def detect(self, current, previous=None):
        previous=previous or {}
        anomalies=[]
        if float(current.get("revenue",0)) < float(previous.get("revenue",0))*0.6 and float(previous.get("revenue",0))>0:
            anomalies.append("revenue_drop")
        if float(current.get("variable_costs",0)) > max(1.0,float(previous.get("variable_costs",0)))*1.5:
            anomalies.append("variable_cost_spike")
        if float(current.get("acquisition_spend",0)) > 0 and int(current.get("paying_customers",0)) == 0:
            anomalies.append("spend_without_customers")
        return {"anomalies":anomalies,"has_anomaly":bool(anomalies)}
