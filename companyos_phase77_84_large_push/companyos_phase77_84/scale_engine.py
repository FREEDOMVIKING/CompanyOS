class ScaleEngine:
    """82: evidence-gated scaling recommendations."""
    def evaluate(self,kpis):
        growth=float(kpis.get("growth",0)); retention=float(kpis.get("retention",0))
        margin=float(kpis.get("margin",0)); reliability=float(kpis.get("reliability",0))
        score=growth*.25+retention*.30+margin*.20+reliability*.25
        return {"scale_score":round(score,4),"recommendation":"scale_carefully" if score>=.75 else
                "optimize_before_scale" if score>=.5 else "do_not_scale","automatic_external_scaling":False}
