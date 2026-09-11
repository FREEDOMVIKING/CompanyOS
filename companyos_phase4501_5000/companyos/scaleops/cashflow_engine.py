class CashflowEngine:
    def evaluate(self, opening_cash, inflows, outflows):
        inflows=float(inflows); outflows=float(outflows); opening_cash=float(opening_cash)
        net=inflows-outflows
        return {
            "opening_cash":opening_cash,
            "inflows":inflows,
            "outflows":outflows,
            "net_cashflow":round(net,2),
            "closing_cash":round(opening_cash+net,2)
        }
