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


def test_pinned_version_beats_the_alias():
    payload = {"aliases": [{"alias_name": "Champion", "version_num": 4}]}
    assert served.resolve_version(payload, "Champion", "13") == "13"
    assert served.resolve_version(payload, "Champion", "") == "4"


def test_champion_command_names_the_version():
    command = served.champion_alias_command("dbw_iris_ml_dev.prod.iris_species", "13")
    assert command[:3] == [
        "api",
        "post",
        "/api/2.1/unity-catalog/models/dbw_iris_ml_dev.prod.iris_species/aliases/Champion",
    ]
    assert '"version_num": 13' in command[-1]


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
        "ARM_CLIENT_ID",
        "ARM_CLIENT_SECRET",
        "ARM_TENANT_ID",
    ]
    complete = {
        "DATABRICKS_HOST": "https://example",
        "ARM_CLIENT_ID": "abc",
        "ARM_CLIENT_SECRET": "secret",
        "ARM_TENANT_ID": "tenant",
    }
    assert auth.missing(complete) == []
    monkeypatch.setenv("DATABRICKS_HOST", "https://example")
    monkeypatch.setenv("ARM_CLIENT_ID", "abc")
    monkeypatch.setenv("ARM_CLIENT_SECRET", "secret")
    monkeypatch.setenv("ARM_TENANT_ID", "tenant")
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN", "dapi-not-printed")
    assert auth.main() == 1
    monkeypatch.delenv("DATABRICKS_TOKEN")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "not-the-entra-app")
    assert auth.main() == 1
    monkeypatch.delenv("DATABRICKS_CLIENT_ID")
    assert auth.main() == 0
