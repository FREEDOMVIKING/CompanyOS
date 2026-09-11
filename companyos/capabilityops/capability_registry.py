class CapabilityRegistry:
    DEFAULTS = {
        "reasoning": {"kind":"provider","required_env":["COMPANYOS_REASONING_URL"]},
        "research": {"kind":"provider","required_env":["COMPANYOS_RESEARCH_URL"]},
        "communications": {"kind":"provider","required_env":["COMPANYOS_COMMUNICATIONS_URL"]},
        "deployment": {"kind":"provider","required_env":["COMPANYOS_DEPLOY_URL"]},
        "finance_read": {"kind":"provider","required_env":["COMPANYOS_FINANCE_READ_URL"]},
    }

    def build(self, overrides=None):
        data = {k:dict(v) for k,v in self.DEFAULTS.items()}
        for k,v in (overrides or {}).items():
            data[k] = {**data.get(k,{}), **v}
        return data
