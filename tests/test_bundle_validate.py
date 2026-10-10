"""Bundle validate falls back when a workspace resource is gone."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "bundle_validate", REPO_ROOT / "scripts" / "bundle_validate.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_schema_error_still_fails():
    module = _module()

    def runner(_target: str) -> tuple[int, str]:
        return 1, "Error: unknown field 'not_a_resource' is not allowed"

    assert module.validate_targets(["develop"], allow_missing=True, runner=runner) == 1


def test_deleted_catalog_is_skipped_when_allowed():
    module = _module()
    seen: list[str] = []

    def runner(target: str) -> tuple[int, str]:
        seen.append(target)
        return 1, "Error: Catalog 'dbw_iris_ml_dev' does not exist."

    assert module.validate_targets(["develop", "ppe"], allow_missing=True, runner=runner) == 0
    assert seen == ["develop", "ppe"]


def test_deleted_catalog_fails_without_allow_missing():
    module = _module()

    def runner(_target: str) -> tuple[int, str]:
        return 1, "Error: Catalog 'dbw_iris_ml_dev' does not exist."

    assert module.validate_targets(["prod"], allow_missing=False, runner=runner) == 1


def test_missing_cli_fails():
    module = _module()

    def runner(_target: str) -> tuple[int, str]:
        raise FileNotFoundError("databricks")

    assert module.validate_targets(["develop"], allow_missing=True, runner=runner) == 1


def test_auth_failure_skips_only_when_allowed():
    module = _module()

    def runner(_target: str) -> tuple[int, str]:
        return 1, "Error: default auth: cannot configure default credentials"

    assert module.validate_targets(["develop"], allow_missing=True, runner=runner) == 0
    assert module.validate_targets(["develop"], allow_missing=False, runner=runner) == 1


def test_forbidden_identity_skips_when_allowed():
    module = _module()

    def runner(_target: str) -> tuple[int, str]:
        return 1, "HTTP Status: 403 Forbidden\nAPI message: Invalid Authorization"

    assert module.validate_targets(["develop"], allow_missing=True, runner=runner) == 0
