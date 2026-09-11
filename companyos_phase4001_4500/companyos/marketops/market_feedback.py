class MarketFeedbackLoop:
    def synthesize(self, signals, customers, sales, experiments):
        return {
            "market_signals":len(signals or []),
            "customer_segments":len(customers or []),
            "sales_actions":len(sales or []),
            "experiment_results":len(experiments or []),
            "next_learning_focus":"highest_uncertainty_with_revenue_impact"
        }
