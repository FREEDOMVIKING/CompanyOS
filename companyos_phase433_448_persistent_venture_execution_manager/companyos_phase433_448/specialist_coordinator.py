class SpecialistCoordinator:
    """437: coordinate specialist jobs and dependencies."""

    def ready_jobs(self, jobs, completed_ids=None):
        completed = set(completed_ids or [])
        ready = []
        for job in jobs:
            deps = set(job.get("depends_on") or [])
            if deps.issubset(completed):
                ready.append(job)
        return ready
