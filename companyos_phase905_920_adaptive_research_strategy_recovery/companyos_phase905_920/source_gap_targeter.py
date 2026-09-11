class SourceGapTargeter:
    """910: identify missing source classes to force diversity."""
    TARGET=["official","reputable_news","public_web","competitor_site","github"]
    def missing(self,evidence):
        have={e.get("source_class","unknown") for e in (evidence or []) if isinstance(e,dict)}
        return [x for x in self.TARGET if x not in have]
