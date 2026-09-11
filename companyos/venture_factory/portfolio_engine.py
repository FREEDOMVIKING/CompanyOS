class PortfolioEngine:
    def decide(self, ventures):
        out=[]
        for v in ventures or []:
            s=float(v.get("score",0))
            growth=float(v.get("growth",0))
            reliability=float(v.get("reliability",0))
            if s>=.75 and growth>=.2 and reliability>=.7: d="SCALE"
            elif s>=.55: d="OPTIMIZE"
            elif s>=.35: d="OBSERVE"
            else: d="RETIRE"
            out.append({**v,"decision":d})
        return out
