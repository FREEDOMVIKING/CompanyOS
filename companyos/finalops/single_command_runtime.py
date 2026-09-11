class SingleCommandRuntime:
    def commands(self):
        return {
            "status":"bash ~/companyos/scripts/companyos_final.sh status",
            "verify":"bash ~/companyos/scripts/companyos_final.sh verify",
            "cycle":"bash ~/companyos/scripts/companyos_final.sh cycle",
            "readiness":"bash ~/companyos/scripts/companyos_final.sh readiness"
        }
