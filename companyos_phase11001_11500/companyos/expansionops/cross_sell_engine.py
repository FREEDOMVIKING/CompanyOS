class CrossSellEngine:
    def recommend(self, customer_portfolio, venture_offers):
        recs=[]
        owned=set(customer_portfolio.get("ventures",[]))
        interests=set(customer_portfolio.get("interests",[]))
        for offer in venture_offers or []:
            if offer.get("venture_id") in owned:
                continue
            tags=set(offer.get("tags",[]))
            fit=len(interests & tags)
            if fit:
                recs.append({**offer,"fit_score":fit})
        return sorted(recs,key=lambda x:x["fit_score"],reverse=True)
