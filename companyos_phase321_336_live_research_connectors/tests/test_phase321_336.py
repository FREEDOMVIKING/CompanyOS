from companyos_phase321_336 import RSSSource, JSONSource, EvidenceQuality

def test_rss():
    body = b"<rss><channel><item><title>X</title><description>manual pain</description></item></channel></rss>"
    assert RSSSource().parse(body, "s", "u")

def test_json():
    body = b'{"items":[{"title":"X","text":"manual pain"}]}'
    assert JSONSource().parse(body, {"name":"s","url":"u","items_path":"items"})

def test_quality():
    assert EvidenceQuality().score({"title":"x","text":"a"*150,"url":"u","source":"s"}) > 0
