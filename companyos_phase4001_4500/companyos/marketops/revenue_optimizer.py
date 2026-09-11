class RevenueOptimizer:
    def optimize(self, metrics):
        m=metrics or {}
        actions=[]
        if float(m.get("gross_margin",0))<0.6: actions.append("improve_margin")
        if float(m.get("conversion_rate",0))<0.05: actions.append("improve_conversion")
        if float(m.get("retention_rate",0))<0.5: actions.append("improve_retention")
        if float(m.get("arpu_growth",0))<0.1: actions.append("test_packaging_or_upsell")
        if not actions: actions.append("scale_profitable_growth")
        return actions
