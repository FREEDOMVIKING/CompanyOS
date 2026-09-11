class ReleaseCandidate:
    """423: release-candidate gate. Preparation is allowed; irreversible launch is not automatic."""

    def evaluate(self, quality, artifacts):
        required = quality.get("required", [])
        passed = set(quality.get("passed", []))
        missing = [g for g in required if g not in passed]
        ready = not missing and bool(artifacts)
        return {
            "release_candidate_ready":ready,
            "missing_quality_gates":missing,
            "artifact_count":len(artifacts),
            "external_launch_authorized":False,
        }
