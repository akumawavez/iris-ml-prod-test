"""Served version follows the Unity Catalog alias, not a hardcoded pin."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


served = _load("apply_served_version.py")
auth = _load("cd_require_service_principal.py")


def test_alias_version_is_the_served_version():
    payload = {
        "name": "dbw_iris_ml_dev.develop.iris_species",
        "aliases": [
            {"alias_name": "Champion", "version_num": 4},
            {"alias_name": "develop", "version_num": 9},
        ],
    }
    assert served.alias_version(payload, "develop") == "9"


def test_missing_alias_is_refused():
    try:
        served.alias_version({"aliases": []}, "ppe")
    except SystemExit as exc:
        assert exc.code == 1 or "ppe" in str(exc)
    else:
        raise AssertionError("expected SystemExit")


def test_endpoint_config_is_small_cpu_scale_to_zero():
    config = served.endpoint_config("dbw_iris_ml_dev.prod.iris_species", "3")
    entity = config["served_entities"][0]
    assert entity["entity_version"] == "3"
    assert entity["workload_size"] == "Small"
    assert entity["scale_to_zero_enabled"] is True
    assert "auto_capture_config" not in config


def test_served_entity_version_reads_the_first_entity():
    endpoint = {"config": {"served_entities": [{"entity_version": "3"}]}}
    assert served.served_entity_version(endpoint) == "3"
    assert served.served_entity_version({}) == ""


def test_service_principal_fields_are_required_and_a_token_is_rejected(monkeypatch):
    assert auth.missing({}) == [
        "DATABRICKS_HOST",
        "DATABRICKS_CLIENT_ID",
        "DATABRICKS_CLIENT_SECRET",
    ]
    complete = {
        "DATABRICKS_HOST": "https://example",
        "DATABRICKS_CLIENT_ID": "abc",
        "DATABRICKS_CLIENT_SECRET": "secret",
    }
    assert auth.missing(complete) == []
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "abc")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "secret")
    monkeypatch.setenv("DATABRICKS_TOKEN", "dapi-not-printed")
    assert auth.main() == 1
    monkeypatch.delenv("DATABRICKS_TOKEN")
    assert auth.main() == 0
