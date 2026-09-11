class ReleaseCandidate:
    """616: promote only QA-passing builds to release candidate."""

    def create(self, venture_id, qa, artifacts):
        ready = bool(qa.get("passed")) and bool(artifacts)
        return {
            "venture_id":venture_id,
            "release_candidate_ready":ready,
            "artifact_count":len(artifacts or []),
            "qa":qa,
            "external_launch_authorized":False,
        }
