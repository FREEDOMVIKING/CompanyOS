class VendorManager:
    def evaluate(self, vendors):
        out=[]
        for v in vendors or []:
            reliability=float(v.get("reliability",0))
            cost=float(v.get("cost_score",0))
            security=float(v.get("security",0))
            lockin=float(v.get("lockin_risk",0))
            score=reliability*0.35+cost*0.2+security*0.3+(1-lockin)*0.15
            out.append({**v,"vendor_score":round(score,3)})
        return sorted(out,key=lambda x:x["vendor_score"],reverse=True)
