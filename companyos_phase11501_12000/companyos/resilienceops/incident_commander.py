class IncidentCommander:
    def classify(self, incident):
        impact=float(incident.get("impact",0))
        spread=float(incident.get("spread",0))
        severity=impact*.7+spread*.3
        level="SEV1" if severity>=.8 else ("SEV2" if severity>=.5 else "SEV3")
        return {
            "level":level,
            "contain_first":True,
            "steps":["detect","contain","stabilize","recover","verify","learn"]
        }
