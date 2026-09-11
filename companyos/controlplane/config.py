from dataclasses import dataclass
from pathlib import Path
from typing import List
import os

@dataclass
class ServiceSpec:
    name: str
    module: str
    enabled: bool = True

def companyos_home() -> Path:
    return Path(os.environ.get("COMPANYOS_HOME", str(Path.home() / "companyos")))

def runtime_dir() -> Path:
    return companyos_home() / "companyos_runtime" / "controlplane"

def log_dir() -> Path:
    return companyos_home() / "logs"

def _module_exists(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False

def services() -> List[ServiceSpec]:
    return [
        ServiceSpec("executive_18201_18300", "companyos.executive.runtime", _module_exists("companyos.executive.runtime")),
        ServiceSpec("dashboard_18301_18400", "companyos.controlplane.dashboard", True),
        ServiceSpec("opscenter_18501_18700", "companyos.opscenter.runtime", True),
        ServiceSpec("orchestrator_18701_19000", "companyos.orchestrator.runtime", True),
        ServiceSpec("intelligence_19001_19500", "companyos.intelligence.runtime", True),
        ServiceSpec("expansion21_19501_21000", "companyos.expansion.runtime", True),
        ServiceSpec("connectors_21001_22000", "companyos.connectors_live.runtime", True),
        ServiceSpec("api_backbone_22001_23000", "companyos.api_backbone.runtime", True),
        ServiceSpec("opportunity_engine_23001_25000", "companyos.opportunity_engine.runtime", True),
        ServiceSpec("venture_builder_25001_27000", "companyos.venture_builder.runtime", True),
        ServiceSpec("research_agent_30001_35000", "companyos.growth_suite.runtime", True),
ServiceSpec("revenue_engine_30001_35000", "companyos.growth_suite.runtime", True),
ServiceSpec("marketing_intelligence_30001_35000", "companyos.growth_suite.runtime", True),
ServiceSpec("customer_acquisition_30001_35000", "companyos.growth_suite.runtime", True),
ServiceSpec("portfolio_manager_30001_35000", "companyos.growth_suite.runtime", True),
ServiceSpec("self_improvement_30001_35000", "companyos.growth_suite.runtime", True),
ServiceSpec("ceo_planner_30001_35000", "companyos.ceo_planner.runtime", True),
ServiceSpec("launch_engine_30001_35000", "companyos.launch_engine.runtime", True),
ServiceSpec("sales_engine_30001_35000", "companyos.sales_engine.runtime", True),
ServiceSpec("finance_manager_30001_35000", "companyos.finance_manager.runtime", True),
ServiceSpec("learning_engine_30001_35000", "companyos.learning_engine.runtime", True),
ServiceSpec("executive_dashboard_v2_30001_35000", "companyos.executive_dashboard_v2.runtime", True),
        ServiceSpec("executive_memory_35001_40000", "companyos.executive_memory.runtime", True),
ServiceSpec("strategic_planner_35001_40000", "companyos.strategic_planner.runtime", True),
ServiceSpec("project_manager_35001_40000", "companyos.project_manager.runtime", True),
ServiceSpec("workforce_manager_35001_40000", "companyos.workforce_manager.runtime", True),
ServiceSpec("vendor_procurement_35001_40000", "companyos.vendor_procurement.runtime", True),
ServiceSpec("customer_support_35001_40000", "companyos.customer_support.runtime", True),
ServiceSpec("risk_compliance_35001_40000", "companyos.risk_compliance.runtime", True),
ServiceSpec("financial_forecasting_35001_40000", "companyos.financial_forecasting.runtime", True),
ServiceSpec("resource_allocator_35001_40000", "companyos.resource_allocator.runtime", True),
ServiceSpec("multi_company_orchestrator_35001_40000", "companyos.multi_company_orchestrator.runtime", True),
        ServiceSpec("code_generation_40001_50000", "companyos.code_generation.runtime", True),
ServiceSpec("website_deployer_40001_50000", "companyos.website_deployer.runtime", True),
ServiceSpec("domain_orchestrator_40001_50000", "companyos.domain_orchestrator.runtime", True),
ServiceSpec("customer_acquisition_v2_40001_50000", "companyos.customer_acquisition_v2.runtime", True),
ServiceSpec("competitor_intelligence_40001_50000", "companyos.competitor_intelligence.runtime", True),
ServiceSpec("negotiation_engine_40001_50000", "companyos.negotiation_engine.runtime", True),
ServiceSpec("ceo_council_v2_40001_50000", "companyos.ceo_council_v2.runtime", True),
ServiceSpec("memory_graph_40001_50000", "companyos.memory_graph.runtime", True),
ServiceSpec("self_evolution_40001_50000", "companyos.self_evolution.runtime", True),
ServiceSpec("profitability_optimizer_40001_50000", "companyos.profitability_optimizer.runtime", True),
        ServiceSpec("product_factory_v2_60001_70000", "companyos.product_factory_v2.runtime", True),
ServiceSpec("task_delegation_v2_60001_70000", "companyos.task_delegation_v2.runtime", True),
ServiceSpec("crm_automation_v2_60001_70000", "companyos.crm_automation_v2.runtime", True),
ServiceSpec("proposal_contracts_v2_60001_70000", "companyos.proposal_contracts_v2.runtime", True),
ServiceSpec("vendor_bidding_v2_60001_70000", "companyos.vendor_bidding_v2.runtime", True),
ServiceSpec("acquisition_scanner_v2_60001_70000", "companyos.acquisition_scanner_v2.runtime", True),
ServiceSpec("revenue_optimizer_v4_60001_70000", "companyos.revenue_optimizer_v4.runtime", True),
ServiceSpec("qa_recovery_v2_60001_70000", "companyos.qa_recovery_v2.runtime", True),
ServiceSpec("executive_analytics_v3_60001_70000", "companyos.executive_analytics_v3.runtime", True),
ServiceSpec("unified_runtime_controller_60001_70000", "companyos.unified_runtime_controller.runtime", True),
                ServiceSpec("roadmap_execution_bridge_70001_80000", "companyos.roadmap_execution_bridge.runtime", True),
        ServiceSpec("milestone_generator_v3_70001_80000", "companyos.milestone_generator_v3.runtime", True),
        ServiceSpec("specialist_assignment_v3_70001_80000", "companyos.specialist_assignment_v3.runtime", True),
        ServiceSpec("venture_artifact_pipeline_70001_80000", "companyos.venture_artifact_pipeline.runtime", True),
        ServiceSpec("execution_evidence_linker_70001_80000", "companyos.execution_evidence_linker.runtime", True),
        ServiceSpec("progress_sync_v3_70001_80000", "companyos.progress_sync_v3.runtime", True),
        ServiceSpec("venture_validation_engine_70001_80000", "companyos.venture_validation_engine.runtime", True),
        ServiceSpec("launch_readiness_engine_70001_80000", "companyos.launch_readiness_engine.runtime", True),
        ServiceSpec("dashboard_cluster_manager_70001_80000", "companyos.dashboard_cluster_manager.runtime", True),
        ServiceSpec("execution_recovery_manager_70001_80000", "companyos.execution_recovery_manager.runtime", True),
                ServiceSpec("venture_builder_v3_80001_95000", "companyos.venture_builder_v3.runtime", True),
                ServiceSpec("revenue_engine_v6_140001_165000", "companyos.revenue_engine_v6.runtime", True),
                ServiceSpec("product_portfolio_v7_165001_190000", "companyos.product_portfolio_v7.runtime", True),
                ServiceSpec("storefront_sales_v8_190001_220000", "companyos.storefront_sales_v8.runtime", True),
                ServiceSpec("crypto_payment_bridge_v9_220001_250000", "companyos.crypto_payment_bridge_v9.runtime", True),
                ServiceSpec("crypto_checkout_connector_v10_250001_280000", "companyos.crypto_checkout_connector_v10.runtime", True),
        ServiceSpec("supervisor_18301_18400", "companyos.controlplane.supervisor", True),
    ]
