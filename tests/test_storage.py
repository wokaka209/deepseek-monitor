import json

from deepseek_monitor import storage


def test_load_config_uses_default_refresh_interval_for_invalid_value(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"refresh_interval_minutes": "bad"}), encoding="utf-8")
    monkeypatch.setattr(storage, "CONFIG_FILE", config_file)

    config = storage.load_config()

    assert config.refresh_interval_minutes == 30
