class SourceDiversifier:
    """747: encourage evidence from multiple independent source classes."""
    def evaluate(self, evidence):
        classes = {}
        for item in evidence or []:
            cls = item.get("source_class", "unknown")
            classes.setdefault(cls, 0)
            classes[cls] += 1
        return {
            "source_classes": classes,
            "diversified": len([k for k in classes if k != "unknown"]) >= 2,
            "class_count": len(classes),
        }
