class ChurnRiskEngine:
    def evaluate(self, customers):
        out=[]
        for c in customers or []:
            risk=(1-float(c.get("usage",0)))*.35+(1-float(c.get("satisfaction",0)))*.35+float(c.get("support_friction",0))*.2+(1-float(c.get("payment_health",1)))*.1
            out.append({"customer_id":c.get("customer_id"),"churn_risk":round(risk,4),"high_risk":risk>=.6})
        return sorted(out,key=lambda x:x["churn_risk"],reverse=True)
