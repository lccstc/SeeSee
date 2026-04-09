def test_template_config_schema_data_engine():
    from bookkeeping_core.template_engine import TemplateConfig
    raw = '''{
        "version": "data-engine-v1",
        "rules": [
            {"pattern": "【{card_type}】", "type": "section"},
            {"pattern": "{country}={price}({restriction})", "type": "price"}
        ]
    }'''
    config = TemplateConfig.from_json(raw)
    assert config.version == "data-engine-v1"
    assert len(config.rules) == 2
    assert config.rules[0]["type"] == "section"

def test_strict_match_pattern():
    from bookkeeping_core.template_engine import match_pattern
    
    pattern = "{country}={price}({restriction})"
    # Exact match
    res = match_pattern("加拿大=3.4(代码批量问)", pattern)
    assert res == {"country": "加拿大", "price": "3.4", "restriction": "代码批量问"}
    
    # Failing match due to extra space
    res2 = match_pattern("加拿大 = 3.4(代码批量问)", pattern)
    assert res2 is None
