import pytest
import os
import yaml
import stat
from talos_config import ConfigurationLoader, ConfigurationError

def test_loader_defaults():
    loader = ConfigurationLoader("testapp")
    config = loader.load(defaults={"key": "default"})
    assert config["key"] == "default"

def test_loader_file_override(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("key: file\nnested: {val: 1}")
    
    loader = ConfigurationLoader("testapp")
    config = loader.load(config_file=str(f), defaults={"key": "default", "other": "x"})
    
    assert config["key"] == "file"
    assert config["other"] == "x"
    assert config["nested"]["val"] == 1

def test_loader_env_override(monkeypatch):
    monkeypatch.setenv("TALOS__KEY", "env")
    monkeypatch.setenv("TALOS__NESTED__VAL", "99")
    
    loader = ConfigurationLoader("testapp")
    config = loader.load(defaults={"key": "default", "nested": {"val": 1}})
    
    assert config["key"] == "env"
    assert config["nested"]["val"] == "99" # Env vars are strings usually

def test_prod_permissions_check(tmp_path, monkeypatch):
    monkeypatch.setenv("TALOS_ENV", "prod")
    f = tmp_path / "unsafe.yaml"
    f.write_text("key: val")
    
    # Make world writable
    os.chmod(f, stat.S_IRUSR | stat.S_IWUSR | stat.S_IWOTH)
    
    loader = ConfigurationLoader("testapp")
    
    with pytest.raises(ConfigurationError, match="world-writable"):
        loader.load(config_file=str(f))

def test_prod_permissions_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("TALOS_ENV", "prod")
    f = tmp_path / "safe.yaml"
    f.write_text("key: val")
    
    # Make safe (user rw only)
    os.chmod(f, stat.S_IRUSR | stat.S_IWUSR)
    
    loader = ConfigurationLoader("testapp")
    loader.load(config_file=str(f))
