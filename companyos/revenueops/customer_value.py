class CustomerValueEngine:
    def segment(self, customers):
        out=[]
        for c in customers or []:
            value=float(c.get("revenue",0))*float(c.get("retention_probability",0))
            out.append({**c,"expected_customer_value":round(value,2)})
        return sorted(out,key=lambda x:x["expected_customer_value"],reverse=True)
