import hashlib

class TestMissionFactory:
    """721: create deterministic controlled integration missions."""

    def create(self, venture_id="venture_integration_test", mission_type="research", seed="default"):
        raw=f"{venture_id}:{mission_type}:{seed}"
        return {
            "mission_id":"mission_test_" + hashlib.sha256(raw.encode()).hexdigest()[:12],
            "mission_type":mission_type,
            "priority":1.0,
            "attempts":0,
            "blocked_on":[],
            "context":{
                "venture_id":venture_id,
                "integration_test":True,
                "seed":seed,
                "objective":"exercise the unified closed-loop runtime safely",
            },
        }
