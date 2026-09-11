class DecisionSynthesizer:
    def synthesize(self, signals):
        confidence=sum(float(s.get("confidence",.5)) for s in signals or [])/max(1,len(signals or []))
        positive=sum(1 for s in signals or [] if float(s.get("value",0))>0)
        negative=sum(1 for s in signals or [] if float(s.get("value",0))<0)
        if positive>negative and confidence>=.65:
            action="advance"
        elif negative>positive:
            action="repair_or_replan"
        else:
            action="collect_more_evidence"
        return {
            "action":action,
            "confidence":round(confidence,3),
            "positive_signals":positive,
            "negative_signals":negative
        }
