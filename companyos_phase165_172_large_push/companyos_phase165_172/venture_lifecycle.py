class VentureLifecycle:
    """170: autonomously move internal ventures through lifecycle stages."""
    def decide(self, venture):
        traction=float(venture.get("traction",0)); evidence=float(venture.get("evidence",0)); risk=float(venture.get("risk",0))
        if risk>.8: action="pause_and_review"
        elif evidence<.3: action="validate"
        elif traction<.5: action="iterate"
        elif traction<.8: action="grow"
        else: action="scale_internal_capacity"
        return {"venture":venture.get("name"),"action":action,
                "autonomous":action!="pause_and_review"}
