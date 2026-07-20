from typing import Any, Dict, List
class RevenueEngine:
    """73: model pricing/revenue scenarios without moving funds."""
    def scenarios(self, price:float, customers:List[int], variable_cost:float=0):
        price=float(price); variable_cost=float(variable_cost)
        return [{"customers":int(n),"revenue":round(price*n,2),
                 "gross_contribution":round((price-variable_cost)*n,2)} for n in customers]
