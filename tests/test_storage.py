import json

from deepseek_monitor import storage


def test_load_config_uses_default_refresh_interval_for_invalid_value(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"refresh_interval_minutes": "bad"}), encoding="utf-8")
    monkeypatch.setattr(storage, "CONFIG_FILE", config_file)

    config = storage.load_config()

    assert config.refresh_interval_minutes == 30


def test_save_config_does_not_persist_removed_platform_token(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    monkeypatch.setattr(storage, "APP_DIR", tmp_path)
    monkeypatch.setattr(storage, "CONFIG_FILE", config_file)

    storage.save_config(storage.AppConfig(api_key="sk-test"))

    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert "platform_token" not in data
