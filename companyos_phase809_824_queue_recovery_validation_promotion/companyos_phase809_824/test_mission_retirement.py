class TestMissionRetirement:
    """813: retire stale integration test missions from production-like queue."""

    def classify(self, mission):
        ctx = dict((mission or {}).get("context") or {})
        is_test = bool(ctx.get("integration_test")) or str(mission.get("mission_id","")).startswith("mission_test_")
        return {
            "retire": is_test and int(mission.get("attempts",0)) >= 1,
            "is_test": is_test,
        }
