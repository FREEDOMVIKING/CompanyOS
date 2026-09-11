class ExperimentEngine:
    def plan(self, opportunity):
        return [
            {"experiment":"problem_interviews","success_metric":"pain_signal","max_cost":50},
            {"experiment":"landing_page","success_metric":"qualified_interest","max_cost":75},
            {"experiment":"pricing_test","success_metric":"willingness_to_pay","max_cost":75},
            {"experiment":"concierge_mvp","success_metric":"customer_value","max_cost":200},
        ]
