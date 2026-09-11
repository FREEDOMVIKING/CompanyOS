class SalesPipelineEngine:
    """1121-1130: manage lead qualification and sales-stage progression."""
    STAGES=["lead","qualified","demo","proposal","won","lost"]

    def score_lead(self, lead):
        score=0
        score+=25 if lead.get("pain_confirmed") else 0
        score+=25 if lead.get("budget_confirmed") else 0
        score+=20 if lead.get("authority_confirmed") else 0
        score+=20 if lead.get("timeline_confirmed") else 0
        score+=10 if lead.get("engagement_score",0)>=0.7 else 0
        return min(100,score)

    def next_stage(self, lead):
        stage=lead.get("stage","lead")
        score=self.score_lead(lead)
        if stage=="lead" and score>=40: return "qualified"
        if stage=="qualified" and score>=60: return "demo"
        if stage=="demo" and score>=70: return "proposal"
        if stage=="proposal" and lead.get("accepted"): return "won"
        return stage

    def process(self, leads):
        out=[]
        for lead in leads or []:
            row=dict(lead)
            row["score"]=self.score_lead(row)
            row["next_stage"]=self.next_stage(row)
            out.append(row)
        return out
