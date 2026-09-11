from companyos_phase385_400 import ValidationOrchestrator, ResultInterpreter, GoNoGoEngine

def test_validation_plan():
    thesis = {"name":"x","customer":"businesses","core_problem":"manual pain","business_model":{"primary":"SaaS"}}
    assert ValidationOrchestrator().plan(thesis)["success"] is True

def test_result_interpreter():
    thresholds = {"landing_page_visit_min":100,"email_conversion_min":0.08,"interview_count_min":5,
                  "pain_confirm_rate_min":0.6,"willingness_to_pay_confirm_rate_min":0.3,"qualified_leads_min":5}
    result = ResultInterpreter().interpret({"landing_page_visits":120,"qualified_leads":6}, thresholds)
    assert result["pass_ratio"] == 1.0

def test_go():
    assert GoNoGoEngine().decide({"pass_ratio":1.0,"total_checks":3})["decision"] == "go_to_mvp"
