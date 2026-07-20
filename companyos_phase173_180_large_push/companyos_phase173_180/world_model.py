class WorldModel:
    """173: maintain evidence-weighted internal beliefs about business conditions."""
    def update(self, beliefs, observations):
        index={str(b.get("topic")):dict(b) for b in beliefs}
        for o in observations:
            topic=str(o.get("topic","general")); signal=float(o.get("signal",.5)); conf=float(o.get("confidence",.5))
            prior=float(index.get(topic,{}).get("belief",.5))
            weight=max(0,min(1,conf))
            index[topic]={"topic":topic,"belief":round(prior*(1-weight)+signal*weight,4),"last_confidence":weight}
        return list(index.values())
