class RevenueForecastEngine:
    def forecast(self, current_mrr, growth_rate, months=6):
        rows=[]; value=float(current_mrr)
        for m in range(1,int(months)+1):
            value*=1+float(growth_rate)
            rows.append({"month":m,"projected_mrr":round(value,2)})
        return rows
