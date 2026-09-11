class EnterpriseScorecard:
    def evaluate(self, ventures):
        rows=[]
        for v in ventures or []:
            growth=float(v.get("growth",0))
            margin=float(v.get("margin",0))
            retention=float(v.get("retention",0))
            reliability=float(v.get("reliability",0))
            strategic=float(v.get("strategic_fit",0.5))
            score=growth*.25+margin*.2+retention*.2+reliability*.2+strategic*.15
            rows.append({**v,"enterprise_score":round(max(0,min(1,score)),3)})
        return sorted(rows,key=lambda x:x["enterprise_score"],reverse=True)
