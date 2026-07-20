class EconomicsEngine:
    """105: unit-economics and break-even analysis; no fund movement."""
    def analyze(self,price,variable_cost,fixed_cost,customers):
        price=float(price); variable_cost=float(variable_cost); fixed_cost=float(fixed_cost); customers=int(customers)
        contribution=price-variable_cost
        revenue=price*customers
        profit=contribution*customers-fixed_cost
        breakeven=None if contribution<=0 else int((fixed_cost+contribution-1)//contribution)
        return {"revenue":round(revenue,2),"profit":round(profit,2),"contribution":round(contribution,2),
        "break_even_customers":breakeven,"funds_moved":False}
