from .provider_dispatcher import ProviderDispatcher
from .query_transformer import QueryTransformer
class EvidenceCollector:
    """781: execute one provider and normalize collected evidence."""
    def collect(self, provider, query, context=None):
        transformed=QueryTransformer().transform(query,provider)
        result=ProviderDispatcher().dispatch(provider, transformed, context or {})
        items=[]
        for i,item in enumerate(result.get("items",[])):
            row=dict(item) if isinstance(item,dict) else {"text":str(item)}
            row.setdefault("id",f"{provider}_{i}")
            row.setdefault("source_class",provider)
            row.setdefault("provider",provider)
            items.append(row)
        return {**result,"items":items}
