class ExperimentEngine:
    def decide(self, experiments):
        out=[]
        for e in experiments or []:
            confidence=float(e.get("confidence",0)); impact=float(e.get("impact",0))
            result=float(e.get("result",0))
            if confidence>=.7 and result>0: action="scale"
            elif confidence>=.5 and impact>=.5: action="iterate"
            else: action="stop_or_redesign"
            out.append({**e,"action":action})
        return out
