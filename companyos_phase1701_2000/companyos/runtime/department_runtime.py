class DepartmentRuntime:
    def execute(self, department, job):
        return {
            "department":department,
            "job_id":job.get("job_id"),
            "task_type":job.get("task_type"),
            "status":"complete",
            "output":{"message":f"{department} completed {job.get('task_type')}"},
        }
