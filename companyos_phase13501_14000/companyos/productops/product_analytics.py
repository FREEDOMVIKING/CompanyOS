class ProductAnalyticsEngine:
    def summarize(self, metrics):
        return {
            "activation_rate":float(metrics.get("activation_rate",0)),
            "feature_adoption":float(metrics.get("feature_adoption",0)),
            "retention_rate":float(metrics.get("retention_rate",0)),
            "nps_proxy":float(metrics.get("nps_proxy",0)),
            "product_health":round(
                float(metrics.get("activation_rate",0))*.3+
                float(metrics.get("feature_adoption",0))*.25+
                float(metrics.get("retention_rate",0))*.3+
                float(metrics.get("nps_proxy",0))*.15,4)
        }
