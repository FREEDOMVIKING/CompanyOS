class ServiceGraph:
    def build(self):
        return {
            "nodes":[
                "ceo","orchestration","execution","connectors","providerexec",
                "liveintegration","actiongov","marketops","scaleops","hardening"
            ],
            "edges":[
                ["ceo","orchestration"],
                ["orchestration","execution"],
                ["execution","connectors"],
                ["connectors","providerexec"],
                ["providerexec","liveintegration"],
                ["liveintegration","actiongov"],
                ["execution","marketops"],
                ["marketops","scaleops"],
                ["scaleops","hardening"]
            ]
        }
