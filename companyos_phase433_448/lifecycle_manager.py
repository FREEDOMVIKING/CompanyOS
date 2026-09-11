class LifecycleManager:
    """441: explicit venture lifecycle transitions."""

    ALLOWED = {
        "queued":{"building","paused","killed"},
        "building":{"testing","paused","failed"},
        "testing":{"release_candidate","building","failed"},
        "release_candidate":{"launched","paused","killed"},
        "launched":{"measuring","paused","killed"},
        "measuring":{"scaling","iterating","paused","killed"},
        "iterating":{"building","testing","paused","killed"},
        "scaling":{"measuring","paused","killed"},
        "paused":{"queued","building","killed"},
        "failed":{"paused","killed"},
        "killed":set(),
    }

    def transition(self, current, target):
        allowed = self.ALLOWED.get(current, set())
        if target not in allowed:
            return {"success":False,"status":"invalid_transition","current":current,"target":target}
        return {"success":True,"status":"transition_allowed","current":current,"target":target}
