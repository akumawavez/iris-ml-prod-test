"""Service principal and managed identity names stay paired with each environment."""

import json
from pathlib import Path

from iris_model.identities import (
    KEY_VAULT_SERVICE_CONNECTION,
    MANAGED_IDENTITY_NAME,
    SCHEMA_PRIVILEGES,
    client_secret_name,
    service_principal_name,
    unity_catalog_grants,
)
from iris_model.promotion import PROMOTION

ROOT = Path(__file__).resolve().parents[1]


def test_each_environment_has_its_own_service_principal():
    names = [service_principal_name(stage.databricks_target) for stage in PROMOTION]
    assert names == ["sp-iris-develop", "sp-iris-ppe", "sp-iris-prod"]
    develop_writes = {
        grant.full_name
        for grant in unity_catalog_grants()
        if grant.principal_name == "sp-iris-develop" and "CREATE_MODEL" in grant.privileges
    }
    assert develop_writes == {"dbw_iris_ml_dev.develop"}
    assert "CREATE_MODEL" in SCHEMA_PRIVILEGES


def test_managed_identity_can_read_and_cannot_train():
    reads = [
        grant for grant in unity_catalog_grants() if grant.principal_name == MANAGED_IDENTITY_NAME
    ]
    schemas = {grant.full_name for grant in reads if grant.securable_type == "schema"}
    assert schemas == {
        "dbw_iris_ml_dev.develop",
        "dbw_iris_ml_dev.ppe",
        "dbw_iris_ml_dev.prod",
    }
    for grant in reads:
        assert "CREATE_MODEL" not in grant.privileges
        assert "MODIFY" not in grant.privileges


def test_checked_in_client_ids_match_the_promotion_targets():
    record = json.loads((ROOT / "infra" / "identities.json").read_text(encoding="utf-8"))
    by_target = {row["databricks_target"]: row for row in record["service_principals"]}
    assert record["managed_identity"]["name"] == MANAGED_IDENTITY_NAME
    assert record["managed_identity"]["service_connection"] == KEY_VAULT_SERVICE_CONNECTION
    assert client_secret_name("develop") == "sp-iris-develop-client-secret"
    blob = json.dumps(record)
    assert "password" not in blob
    for stage in PROMOTION:
        row = by_target[stage.databricks_target]
        assert row["name"] == service_principal_name(stage.databricks_target)
        assert row["variable_group"] == stage.variable_group
        target = (ROOT / "databricks" / "targets" / f"{stage.databricks_target}.yml").read_text(
            encoding="utf-8"
        )
        assert row["client_id"] in target


def test_keyvault_export_masks_the_secret_and_does_not_print_it(tmp_path, monkeypatch, capsys):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "export_keyvault_secret", ROOT / "scripts" / "export_keyvault_secret.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    env_file = tmp_path / "github.env"
    env_file.write_text("", encoding="utf-8")

    class Completed:
        returncode = 0
        stdout = "vault-secret-value\n"
        stderr = ""

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: Completed())
    try:
        module.main(["--target", "develop"])
    except SystemExit as exc:
        assert exc.code == "Pass --github-env. This script does not print the secret."
    else:
        raise AssertionError("missing --github-env must exit")
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    assert module.main(["--target", "develop", "--github-env"]) == 0
    written = env_file.read_text(encoding="utf-8")
    assert "ARM_CLIENT_SECRET<<IRIS_KV_SECRET" in written
    assert "vault-secret-value" in written
    assert "529f55f8-5bbd-4921-b041-5348ed4e741b" in written
    captured = capsys.readouterr()
    assert "::add-mask::vault-secret-value" in captured.out
    assert "Fetched sp-iris-develop-client-secret" in captured.out
