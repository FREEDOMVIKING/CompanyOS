from companyos.runtime.openai_web_search_adapter import _output_text, _sources

def test_parse_output_text_and_sources():
    data={
        "output":[
            {
                "type":"web_search_call",
                "action":{"sources":[
                    {"title":"Official Vendor","url":"https://example.com/pricing"},
                    {"title":"Official Vendor","url":"https://example.com/pricing"},
                ]},
            },
            {
                "type":"message",
                "content":[{"type":"output_text","text":"Official pricing is available at the cited source."}],
            },
        ]
    }
    assert "Official pricing" in _output_text(data)
    src=_sources(data)
    assert len(src)==1
    assert src[0]["url"]=="https://example.com/pricing"
