class DataIntegrityGuard:
    def evaluate(self, checks):
        failed=[c.get("name") for c in checks or [] if not c.get("passed")]
        return {"integrity_ok":not failed,"failed_checks":failed}
