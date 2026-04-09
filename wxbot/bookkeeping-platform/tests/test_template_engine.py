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
