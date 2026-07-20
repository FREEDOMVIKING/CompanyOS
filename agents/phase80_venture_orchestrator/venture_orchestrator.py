import json
import sys

from agents.phase65_opportunity_pipeline.opportunity_pipeline import load as load_opportunities
from agents.phase72_opportunity_scoring.opportunity_scoring import score_factors
from agents.phase73_business_architect.business_architect import design_business
from agents.phase74_mvp_designer.mvp_designer import design_mvp
from agents.phase75_validation_engine.validation_engine import build_validation_plan
from agents.phase76_revenue_engine.revenue_engine import model_revenue
from agents.phase77_launch_readiness.launch_readiness import assess
from agents.phase70_ceo_command_center.ceoctl import dashboard as ceo_dashboard

def evaluate_best():
    data = load_opportunities()
    opportunities = data.get("opportunities", [])
    if not opportunities:
        return {
            "success": True,
            "status": "phase80_no_opportunities",
            "message": "Add opportunities to Phase 65 before running venture evaluation.",
        }

    # Use stored Phase 65 score as a baseline signal without inventing external evidence.
    ranked = sorted(opportunities, key=lambda x: int(x.get("score", 0)), reverse=True)
    best = ranked[0]

    factors = {
        "market_need": best.get("score", 50),
        "speed_to_revenue": best.get("score", 50),
        "automation_potential": best.get("score", 50),
        "competition_advantage": min(100, int(best.get("score", 50))),
        "execution_feasibility": best.get("score", 50),
    }
    composite, normalized = score_factors(factors)
    architecture = design_business(best)
    mvp = design_mvp(architecture)
    validation = build_validation_plan(best.get("title", "Opportunity"))
    revenue = model_revenue()
    readiness = assess({
        "problem_validated": False,
        "customer_defined": False,
        "mvp_tested": False,
        "revenue_path_defined": True,
        "risk_review_complete": False,
        "approval_boundary_clear": True,
    })

    return {
        "success": True,
        "status": "phase80_venture_evaluation_complete",
        "selected_opportunity": best,
        "baseline_score": composite,
        "scoring_factors": normalized,
        "business_architecture": architecture,
        "mvp_design": mvp,
        "validation_plan": validation,
        "revenue_model": revenue,
        "launch_readiness": readiness,
        "external_action_taken": False,
    }

def dashboard():
    return {
        "success": True,
        "status": "phase80_venture_orchestrator_dashboard",
        "ceo": ceo_dashboard(),
    }

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "dashboard"
    if cmd == "dashboard":
        result = dashboard()
    elif cmd == "evaluate":
        result = evaluate_best()
    else:
        result = {
            "success": False,
            "status": "unknown_command",
            "available_commands": ["dashboard", "evaluate"],
        }
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
