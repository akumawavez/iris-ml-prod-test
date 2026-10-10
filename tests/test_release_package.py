"""Release wheel build and gated bundle deploy."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_project_version_reads_pyproject():
    module = _load("release_package")
    assert module.project_version(REPO_ROOT / "pyproject.toml") == "0.1.0"


def test_build_wheel_requires_the_versioned_file(tmp_path: Path):
    module = _load("release_package")
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nversion = "0.1.0"\n', encoding="utf-8")

    def runner(root: Path, version: str) -> None:
        dist = root / "dist"
        dist.mkdir()
        (dist / f"iris_model-{version}-py3-none-any.whl").write_bytes(b"wheel")

    wheel = module.build_wheel(tmp_path, runner=runner)
    assert wheel.name == "iris_model-0.1.0-py3-none-any.whl"


def test_build_wheel_fails_when_the_wheel_is_missing(tmp_path: Path):
    module = _load("release_package")
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nversion = "0.1.0"\n', encoding="utf-8")

    def runner(_root: Path, _version: str) -> None:
        return None

    try:
        module.build_wheel(tmp_path, runner=runner)
    except SystemExit as exc:
        assert "0.1.0" in str(exc)
    else:
        raise AssertionError("missing wheel should exit")


def test_deploy_skips_a_missing_workspace_and_fails_a_schema_error():
    module = _load("bundle_deploy")

    def unavailable(output: str, *, allow_auth: bool) -> bool:
        return allow_auth and "does not exist" in output

    def missing(_target: str) -> tuple[int, str]:
        return 1, "Catalog 'dbw_iris_ml_dev' does not exist."

    def schema(_target: str) -> tuple[int, str]:
        return 1, "Error: unknown field is not allowed"

    assert (
        module.deploy_target("develop", allow_missing=True, runner=missing, unavailable=unavailable)
        == 0
    )
    assert (
        module.deploy_target("develop", allow_missing=True, runner=schema, unavailable=unavailable)
        == 1
    )
