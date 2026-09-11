class AgentPerformanceManager:
    def evaluate(self, results):
        rows=[]
        for r in results or []:
            quality=float(r.get("quality",0.5))
            speed=float(r.get("speed",0.5))
            reliability=float(r.get("reliability",0.5))
            learning=float(r.get("learning",0.5))
            score=quality*0.35+speed*0.2+reliability*0.3+learning*0.15
            action="retain"
            if score<0.4: action="coach_or_replace"
            elif score>0.8: action="expand_scope"
            rows.append({**r,"performance_score":round(score,3),"management_action":action})
        return rows
