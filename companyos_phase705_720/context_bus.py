class ContextBus:
    """707: merge stage outputs into one persistent execution context."""

    def merge(self, context, payload):
        context = dict(context or {})
        payload = dict(payload or {})
        for key, value in payload.items():
            if isinstance(value, dict) and isinstance(context.get(key), dict):
                merged = dict(context[key])
                merged.update(value)
                context[key] = merged
            else:
                context[key] = value
        return context
