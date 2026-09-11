class ReleaseManifest:
    def create(self, artifact, tests, scans):
        return {
            "artifact": artifact,
            "tests": tests,
            "scans": scans,
            "promotion_ready": bool(tests.get("passed")) and bool(scans.get("passed"))
        }
