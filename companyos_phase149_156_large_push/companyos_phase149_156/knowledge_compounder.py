class KnowledgeCompounder:
    """153: turn repeated evidence into reusable operating knowledge."""
    def compound(self, observations):
        grouped={}
        for o in observations:
            key=str(o.get("topic","general"))
            grouped.setdefault(key,[]).append(o)
        return [{"topic":k,"observation_count":len(v),"confidence":round(sum(float(x.get("confidence",0)) for x in v)/len(v),4)}
                for k,v in grouped.items()]
