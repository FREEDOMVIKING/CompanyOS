class ConfidenceDeltaTracker:
    def calculate(self,before,after):
        b=float(before or 0); a=float(after or 0)
        return {"before":b,"after":a,"delta":round(a-b,3),"improved":a>b}
