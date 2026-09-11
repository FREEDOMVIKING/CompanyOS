class GrowthForecaster:
    def forecast(self, current_revenue, monthly_growth, months=6):
        value=float(current_revenue); rate=float(monthly_growth)
        points=[]
        for month in range(1,int(months)+1):
            value*=1+rate
            points.append({"month":month,"projected_revenue":round(value,2)})
        return {"forecast":points,"ending_revenue":round(value,2)}
