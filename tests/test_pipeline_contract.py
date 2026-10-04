from pathlib import Path

import yaml

PIPELINE = Path("azure-pipelines.yml").read_text(encoding="utf-8")
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_runs_pytest_and_does_not_deploy():
    assert "pytest" in PIPELINE
    assert "databricks bundle deploy" not in PIPELINE
    assert "develop" in PIPELINE


def _bundle_targets():
    targets = {}
    for path in sorted(Path("databricks/targets").glob("*.yml")):
        targets.update(yaml.safe_load(path.read_text(encoding="utf-8"))["targets"])
    return targets


def test_bundle_describes_one_develop_endpoint_and_does_not_select_later_targets():
    bundle = yaml.safe_load(Path("databricks.yml").read_text(encoding="utf-8"))
    include = "\n".join(bundle["include"])
    assert "databricks/jobs/" in include
    assert "databricks/targets/" in include
    assert "databricks/tasks/" in include
    assert Path("databricks/artifacts/iris_endpoint.yml").is_file()
    targets = _bundle_targets()
    endpoint = yaml.safe_load(
        Path("databricks/artifacts/iris_endpoint.yml").read_text(encoding="utf-8")
    )
    assert targets["develop"]["default"] is True
    assert targets["ppe"]["workspace"]["host"] == ""
    assert targets["prod"]["workspace"]["host"] == ""
    served = endpoint["resources"]["model_serving_endpoints"]["iris_species_dev"]
    assert served["name"] == "iris-species-dev"
    entity = served["config"]["served_entities"][0]
    assert entity["workload_size"] == "Small"
    assert entity["scale_to_zero_enabled"] is True
    # Legacy inference tables are rejected even with enabled=false.
    assert served["config"].get("auto_capture_config") in (None, {"enabled": False})
    text = Path("azure-pipelines.yml").read_text(encoding="utf-8")
    assert "databricks bundle deploy" not in text


def test_github_ci_runs_pytest_only_when_required():
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "pytest" in ci
    assert "databricks bundle deploy" not in ci
    assert "develop" in ci
    # uv-only toolchain: sync the lockfile, never pip-install requirements.
    assert "uv sync --locked" in ci
    assert "uv run pytest" in ci
    assert "ruff" in ci
    assert "pip install -r requirements" not in ci
    assert "uv.lock" in ci
    # Runs only when required: path-scoped, one ref at a time, never scheduled.
    assert "paths:" in ci
    assert "notebooks/**" in ci
    assert "concurrency" in ci
    workflow = yaml.safe_load(ci)
    # NOTE: PyYAML parses the `on:` key as boolean True (YAML 1.1).
    triggers = workflow.get(True, workflow.get("on", {}))
    assert "pull_request" in triggers
    assert "push" in triggers
    assert "schedule" not in triggers
    assert "workflow_dispatch" not in triggers


def test_azure_ci_runs_only_when_required():
    pipeline = yaml.safe_load(PIPELINE)
    assert "pytest" in PIPELINE
    assert "databricks bundle deploy" not in PIPELINE
    # uv-only toolchain: sync the lockfile, never pip-install requirements.
    assert "uv sync --locked" in PIPELINE
    assert "uv run pytest" in PIPELINE
    assert "ruff" in PIPELINE
    assert "pip install -r requirements" not in PIPELINE
    # Batch collapses superseded pushes; PRs stay develop-only; no schedules.
    assert pipeline["trigger"]["batch"] is True
    assert pipeline["pr"]["branches"]["include"] == ["develop"]
    assert "schedules" not in pipeline
    trigger_paths = pipeline["trigger"]["paths"]
    assert "src/*" in trigger_paths["include"]
    assert "notebooks/*" in trigger_paths["include"]
    assert "uv.lock" in trigger_paths["include"]
    assert "docs/*" in trigger_paths["exclude"]


def test_uv_project_layout():
    import tomllib

    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["name"] == "iris-model"
    assert "mlflow" in str(project["dependencies"])
    assert "pytest" in str(project["optional-dependencies"]["dev"])
    assert (REPO_ROOT / "uv.lock").exists()
    assert "iris-model" in (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")
    assert (REPO_ROOT / ".python-version").exists()
    frozen = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "uv pip compile --universal" in frozen
    assert 'pywin32==312 ; sys_platform == "win32"' in frozen.replace("'", '"')


def test_cd_is_manual_only_and_gated():
    cd = yaml.safe_load((REPO_ROOT / "azure-pipelines-cd.yml").read_text(encoding="utf-8"))
    assert cd["trigger"] == "none"
    assert cd["pr"] == "none"
    deploy_text = (REPO_ROOT / "azure-pipelines-cd.yml").read_text(encoding="utf-8")
    assert "environment: iris-develop" in deploy_text
    assert "group: iris-develop" in deploy_text
    assert "databricks bundle deploy -t develop" in deploy_text
    assert "-t ppe" not in deploy_text
    assert "-t prod" not in deploy_text

    gh_cd_text = (REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
    gh_cd = yaml.safe_load(gh_cd_text)
    gh_triggers = gh_cd.get(True, gh_cd.get("on", {}))
    assert list(gh_triggers) == ["workflow_dispatch"]
    assert "environment: develop" in gh_cd_text
    # CI stays test-only and never calls the CD path.
    assert "databricks bundle deploy" not in PIPELINE
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "databricks bundle deploy" not in ci


def test_cd_databricks_deployment_pipeline_implementation():
    az_cd_text = (REPO_ROOT / "azure-pipelines-cd.yml").read_text(encoding="utf-8")
    az_cd = yaml.safe_load(az_cd_text)
    assert az_cd["trigger"] == "none"
    assert az_cd["pr"] == "none"
    assert "checkout: self" in az_cd_text
    assert (
        "databricks/setup-cli" in az_cd_text
        or "install.sh" in az_cd_text
        or "databricks_cli_" in az_cd_text
    )
    assert "databricks bundle validate -t develop" in az_cd_text
    assert "databricks bundle deploy -t develop" in az_cd_text
    assert "databricks bundle run iris-ml-job-pipeline -t develop" in az_cd_text
    assert "databricks serving-endpoints get iris-species-dev" in az_cd_text
    assert "test_serving.py --endpoint iris-species-dev" in az_cd_text

    gh_cd_text = (REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
    gh_cd = yaml.safe_load(gh_cd_text)
    assert "workflow_dispatch" in str(gh_cd)
    assert "databricks/setup-cli@v1.19.0" in gh_cd_text
    assert "pip install databricks-cli" not in gh_cd_text
    assert "databricks bundle validate -t develop" in gh_cd_text
    assert "databricks bundle deploy -t develop" in gh_cd_text
    assert "databricks bundle run iris-ml-job-pipeline -t develop" in gh_cd_text
    assert "databricks serving-endpoints get iris-species-dev" in gh_cd_text
    assert "test_serving.py --endpoint iris-species-dev" in gh_cd_text
    assert '"name": "iris-species-dev"' in az_cd_text
    assert '"name": "iris-species-dev"' in gh_cd_text
    assert "serving-endpoints create iris-species-dev" not in az_cd_text
    assert "serving-endpoints create iris-species-dev" not in gh_cd_text


def test_databricks_bundle_validation_passes():
    import shutil
    import subprocess

    if shutil.which("databricks"):
        result = subprocess.run(
            ["databricks", "bundle", "validate", "-t", "develop"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"databricks bundle validate failed: {result.stderr or result.stdout}"
        )


def test_cost_control_caps_at_ten_dollars():
    tracker = (REPO_ROOT / "docs" / "cost-tracker.md").read_text(encoding="utf-8")
    assert "$10.00" in tracker
    assert "50%" in tracker and "80%" in tracker and "100%" in tracker
    assert "30 min" in tracker
    assert "cost-dashboard.html" in tracker
    dashboard = (REPO_ROOT / "docs" / "cost-dashboard.html").read_text(encoding="utf-8")
    assert "10.00" in dashboard
    bicep = (REPO_ROOT / "infra" / "budget.bicep").read_text(encoding="utf-8")
    assert "Microsoft.Consumption/budgets" in bicep
    assert "param monthlyCap int = 10" in bicep
    setup = (REPO_ROOT / "scripts" / "setup_budget.ps1").read_text(encoding="utf-8")
    assert "-Confirm" in setup
    assert "MonthlyCap = 10" in setup
    snapshot = (REPO_ROOT / "scripts" / "cost_snapshot.ps1").read_text(encoding="utf-8")
    assert "az consumption usage list" in snapshot
    assert "group delete" not in snapshot


def test_shutdown_guide_and_script_exist_and_are_guarded():
    guide = (REPO_ROOT / "docs" / "teardown-and-restore.md").read_text(encoding="utf-8")
    assert "disable" in guide.lower()
    assert "backup" in guide.lower()
    # Disable-before-delete order: backup/stop/disable sections precede delete.
    assert guide.lower().index("disable") < guide.lower().rindex("delete the resource group")
    script = (REPO_ROOT / "scripts" / "teardown_dev.ps1").read_text(encoding="utf-8")
    assert "-Confirm" in script
    assert "-IncludeDelete" in script
    assert "az group delete" in script  # present but gated behind -IncludeDelete
    assert "backup" in script.lower()


def test_serving_test_script_is_safe_by_default():
    script = (REPO_ROOT / "scripts" / "test_serving.py").read_text(encoding="utf-8")
    assert "dry" in script.lower()
    assert "DATABRICKS_TOKEN" in script
    assert "os.environ.get" in script  # env-only auth, never argv/files
    assert "argparse" in script
    assert "/serving-endpoints/" in script and "/invocations" in script
    doc = (REPO_ROOT / "docs" / "serving-inference-test.md").read_text(encoding="utf-8")
    assert "test_serving.py --dry-run" in doc
    assert "iris-species-dev/invocations" in doc
    assert "setosa" in doc and "virginica" in doc
