class ConfigValidator:
    def validate(self, config, required=None):
        config=config or {}
        missing=[k for k in (required or []) if k not in config]
        unsafe=[]
        if config.get("max_parallel",1)>64: unsafe.append("max_parallel_too_high")
        if config.get("retry_limit",3)>10: unsafe.append("retry_limit_too_high")
        return {"valid":not missing and not unsafe,"missing":missing,"unsafe":unsafe}
