class IdleWorkGenerator:
    """203: generate useful autonomous work whenever execution capacity would be idle."""
    DEFAULTS=["review_metrics","inspect_failures","consolidate_memory","research_opportunities","improve_tests"]
    def generate(self,active_count,capacity):
        slots=max(0,int(capacity)-int(active_count))
        return [{"task":self.DEFAULTS[i%len(self.DEFAULTS)],"autonomous":True,"idle_fill":True}
                for i in range(slots)]
