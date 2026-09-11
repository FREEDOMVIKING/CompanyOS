class IncidentManager:
    def classify(self, signals):
        incidents=[]
        for s in signals or []:
            severity="low"
            if s.get("critical"): severity="critical"
            elif float(s.get("impact",0))>=.7: severity="high"
            elif float(s.get("impact",0))>=.4: severity="medium"
            action={
                "critical":"safe_stop_and_recover",
                "high":"isolate_and_repair",
                "medium":"repair_and_monitor",
                "low":"monitor"
            }[severity]
            incidents.append({**s,"severity":severity,"recommended_action":action})
        return incidents
