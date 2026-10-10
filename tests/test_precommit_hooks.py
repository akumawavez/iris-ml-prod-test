"""Local pre-commit hooks that protect secrets, tokens, and test-only CI."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts" / "precommit"


def _load(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


secret_files = _load("forbid_secret_files.py")
token_literals = _load("forbid_token_literals.py")
ci_deploy = _load("forbid_ci_deploy.py")


def test_secret_filenames_are_blocked_and_example_is_allowed():
    assert secret_files.is_blocked(".agents/mcp_config.json")
    assert not secret_files.is_blocked(".agents/mcp_config.example.json")
    assert secret_files.is_blocked(".env")
    assert secret_files.is_blocked("config/.env.local")
    assert secret_files.is_blocked("certs/workspace.pem")
    assert secret_files.is_blocked("id_rsa")
    assert secret_files.is_blocked("backup/2026-10-08-zero-cost/keyvault-secrets.json")
    assert secret_files.is_blocked("pipeline-secrets.json")
    assert not secret_files.is_blocked(".env.example")
    assert not secret_files.is_blocked("docs/secrets.md")


def test_token_literals_match_shapes_not_names():
    assert token_literals.findings("a.py", "token = 'dapi" + "ab" * 16 + "'")
    assert token_literals.findings("a.py", "ghp_" + "a" * 20)
    assert token_literals.findings("a.py", "-----BEGIN " + "PRIVATE KEY-----")
    assert token_literals.findings("a.md", "DATABRICKS_TOKEN") == []
    assert token_literals.findings("a.md", "github-token") == []


def test_ci_files_cannot_deploy_or_run_jobs():
    assert ci_deploy.violations("databricks bundle validate -t develop") == []
    assert "databricks bundle deploy" in ci_deploy.violations("databricks bundle deploy -t develop")
    assert "databricks bundle run" in ci_deploy.violations(
        "databricks bundle run iris-ml-job-pipeline"
    )


def test_precommit_config_lists_the_project_hooks():
    text = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    for hook_id in (
        "ruff",
        "ruff-format",
        "detect-private-key",
        "check-merge-conflict",
        "check-added-large-files",
        "check-ast",
        "debug-statements",
        "no-commit-to-branch",
        "trailing-whitespace",
        "end-of-file-fixer",
        "mixed-line-ending",
        "check-illegal-windows-names",
        "check-executables-have-shebangs",
        "forbid-secret-files",
        "forbid-token-literals",
        "forbid-ci-deploy",
        "pytest-pre-push",
    ):
        assert f"id: {hook_id}" in text
    assert "[--branch, develop, --branch, ppe, --branch, main]" in text
    assert "default_install_hook_types: [pre-commit, pre-push]" in text
    assert "default_stages: [pre-commit]" in text
    assert "stages: [pre-push]" in text
