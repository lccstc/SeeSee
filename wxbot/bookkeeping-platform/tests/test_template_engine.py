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

def test_parse_message_strict():
    from bookkeeping_core.template_engine import TemplateConfig, parse_message_with_template
    
    text = "【XBOX】\n加拿大=3.4(代码批量问)\n10-1000=5.2\n未知格式=1.0"
    config = TemplateConfig(
        version="data-engine-v1",
        rules=[
            {"pattern": "【{card_type}】", "type": "section"},
            {"pattern": "{country}={price}({restriction})", "type": "price"},
            {"pattern": "{amount}={price}", "type": "price"}
        ]
    )
    
    doc = parse_message_with_template(text, config, source_group_key="G1")
    assert len(doc.rows) == 2
    assert doc.rows[0].country_or_currency == "加拿大"
    assert doc.rows[0].price == 3.4
    assert doc.rows[0].card_type == "XBOX"
    
    assert doc.rows[1].amount_range == "10-1000"
    assert doc.rows[1].price == 5.2
    assert doc.rows[1].card_type == "XBOX"
    
    assert len(doc.exceptions) == 1
    assert doc.exceptions[0].source_line == "未知格式=1.0"
