class IncidentDetector:
    """1053-1060: detect incidents from health and business metrics."""
    def detect(self, launch_health, telemetry=None):
        telemetry=telemetry or {}
        incidents=[]
        if not (launch_health or {}).get("healthy",True):
            incidents.append({"type":"service_health","severity":"high"})
        if float(telemetry.get("refund_rate",0))>0.15:
            incidents.append({"type":"refund_spike","severity":"medium"})
        if float(telemetry.get("chargeback_rate",0))>0.03:
            incidents.append({"type":"chargeback_spike","severity":"high"})
        return {"incident":bool(incidents),"incidents":incidents}
