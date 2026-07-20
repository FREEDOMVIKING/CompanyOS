class MarketModel:
    """118: TAM/SAM/SOM planning model."""
    def estimate(self,total_customers,annual_value,serviceable_pct,obtainable_pct):
        tam=max(0,float(total_customers))*max(0,float(annual_value))
        sam=tam*max(0,min(1,float(serviceable_pct)));som=sam*max(0,min(1,float(obtainable_pct)))
        return {"tam":round(tam,2),"sam":round(sam,2),"som":round(som,2)}
