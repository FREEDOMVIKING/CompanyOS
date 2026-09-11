import hashlib

class MissionGenerator:
    """498: generate canonical missions from CEO state and evidence gaps."""

    def _id(self, typ, key):
        return "mission_" + hashlib.sha256(f"{typ}:{key}".encode()).hexdigest()[:12]

    def generate(self, ceo_state, context=None):
        context = context or {}
        stage = ceo_state.get("current_stage", "opportunity")
        missions = []

        if stage == "opportunity":
            missions.append({
                "mission_id": self._id("research", "opportunity"),
                "mission_type": "research",
                "priority": 0.9,
                "attempts": 0,
                "blocked_on": [],
                "context": context,
            })
        elif stage == "validation":
            thesis = context.get("top_thesis") or context.get("thesis")
            blocked = [] if context.get("validation_metrics") else ["validation_evidence"]
            missions.append({
                "mission_id": self._id("validation", str((thesis or {}).get("name","unknown"))),
                "mission_type": "validation",
                "priority": 1.0,
                "attempts": 0,
                "blocked_on": blocked,
                "context": context,
            })
        elif stage == "venture":
            missions.append({
                "mission_id": self._id("venture", str(context.get("venture_id","candidate"))),
                "mission_type": "venture",
                "priority": 0.95,
                "attempts": 0,
                "blocked_on": [],
                "context": context,
            })
        elif stage == "build":
            missions.append({
                "mission_id": self._id("build", str(context.get("venture_id","candidate"))),
                "mission_type": "build",
                "priority": 0.95,
                "attempts": 0,
                "blocked_on": [],
                "context": context,
            })
        elif stage == "operations":
            blocked = [] if context.get("operating_metrics") else ["operations_metrics"]
            missions.append({
                "mission_id": self._id("operations", str(context.get("venture_id","candidate"))),
                "mission_type": "operations",
                "priority": 0.85,
                "attempts": 0,
                "blocked_on": blocked,
                "context": context,
            })
        elif stage == "portfolio":
            missions.append({
                "mission_id": self._id("portfolio", "portfolio"),
                "mission_type": "portfolio",
                "priority": 0.8,
                "attempts": 0,
                "blocked_on": [],
                "context": context,
            })

        return missions
