class ExperimentDesigner:
    """387: create cheap evidence-first experiments."""

    def design(self, thesis):
        return [
            {"type":"customer_interview","goal":"confirm problem severity and frequency"},
            {"type":"landing_page","goal":"measure interest and conversion intent"},
            {"type":"offer_test","goal":"test willingness to pay"},
            {"type":"concierge_prototype","goal":"test outcome value before full automation"},
        ]
