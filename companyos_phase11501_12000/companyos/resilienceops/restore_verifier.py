class RestoreVerifier:
    def verify(self, backup, restore):
        checks={
            "exists":bool(restore),
            "checksum":backup.get("checksum")==restore.get("checksum"),
            "schema":backup.get("schema_version")==restore.get("schema_version")
        }
        return {"verified":all(checks.values()),"checks":checks}
