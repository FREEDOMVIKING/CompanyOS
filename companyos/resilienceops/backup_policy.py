class BackupPolicy:
    def evaluate(self, asset):
        criticality=asset.get("criticality","medium")
        interval={"critical":15,"high":60,"medium":360,"low":1440}.get(criticality,360)
        return {
            "asset":asset.get("name"),
            "backup_interval_minutes":interval,
            "encrypted":True,
            "versioned":True,
            "restore_test_required":criticality in {"critical","high"}
        }
