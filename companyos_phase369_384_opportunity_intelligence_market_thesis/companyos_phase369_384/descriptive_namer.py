from __future__ import annotations

class DescriptiveNamer:
    """380: replace Opportunity 1/2 labels with descriptive business concepts."""

    NAMES = {
        "estimating_and_proposals": "AI Estimating & Proposal Copilot",
        "workflow_automation": "Workflow Automation Copilot",
        "integration_sync": "Integration & Sync Assistant",
        "cost_reduction": "Software Spend Optimization Assistant",
        "reporting_analytics": "Automated Reporting Intelligence",
        "customer_support": "AI Support Operations Copilot",
        "scheduling_operations": "Smart Scheduling & Dispatch Copilot",
        "compliance_admin": "Compliance Documentation Copilot",
        "other_business_pain": "Business Process Automation Opportunity",
    }

    def name(self, theme):
        return self.NAMES.get(theme, theme.replace("_"," ").title())
