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
    assert bundle["include"] == [
        "databricks/variables.yml",
        "databricks/artifacts/*.yml",
        "databricks/jobs/*.yml",
        "databricks/targets/*.yml",
    ]
    variables = yaml.safe_load(Path("databricks/variables.yml").read_text(encoding="utf-8"))
    assert variables["variables"]["env_suffix"]["default"] == "develop"
    assert variables["variables"]["model_version"]["default"] == "5"
    assert "variables" not in bundle
    assert Path("databricks/artifacts/iris_endpoint.yml").is_file()
    targets = _bundle_targets()
    endpoint = yaml.safe_load(
        Path("databricks/artifacts/iris_endpoint.yml").read_text(encoding="utf-8")
    )
    assert targets["develop"]["default"] is True
    shared_host = "https://adb-7405619226406985.5.azuredatabricks.net"
    assert targets["ppe"]["workspace"]["host"] == shared_host
    assert targets["prod"]["workspace"]["host"] == shared_host
    served = endpoint["resources"]["model_serving_endpoints"]["iris_species"]
    assert served["name"] == "iris-species-${var.env_suffix}"
    entity = served["config"]["served_entities"][0]
    assert entity["entity_name"] == "dbw_iris_ml_dev.${var.env_suffix}.iris_species"
    assert entity["workload_size"] == "Small"
    assert entity["scale_to_zero_enabled"] is True
    assert "auto_capture_config" not in served.get("config", {})
    text = Path("azure-pipelines.yml").read_text(encoding="utf-8")
    assert "databricks bundle deploy" not in text


def _github_triggers(text: str) -> dict:
    workflow = yaml.safe_load(text)
    # NOTE: PyYAML parses the `on:` key as boolean True (YAML 1.1).
    return workflow.get(True, workflow.get("on", {}))


def test_github_ci_is_test_only_and_cd_stays_disabled():
    """GitHub CI may run tests. GitHub CD stays off. Deploy is Azure DevOps only."""
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    ci_triggers = _github_triggers(ci_text)
    assert set(ci_triggers) == {"push", "pull_request"}
    assert "schedule" not in ci_triggers
    assert "workflow_dispatch" not in ci_triggers
    assert ci_triggers["push"]["branches"] == ["develop", "ppe", "main"]
    assert ci_triggers["pull_request"]["branches"] == ["develop", "ppe", "main"]
    ci = yaml.safe_load(ci_text)
    assert ci["permissions"] == {"contents": "read"}
    assert ci["jobs"]
    for job in ci["jobs"].values():
        assert job.get("if") != "${{ false }}"
    assert "databricks bundle deploy" not in ci_text
    assert "databricks bundle validate" not in ci_text
    assert "databricks bundle run" not in ci_text
    assert "uv sync --locked" in ci_text
    assert "uv run pytest" in ci_text
    assert "scripts/release_package.py" in ci_text
    assert "pip install -r requirements" not in ci_text
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in ci_text

    cd_text = (REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
    assert list(_github_triggers(cd_text)) == ["workflow_dispatch"]
    assert "pull_request" not in _github_triggers(cd_text)
    assert "push" not in _github_triggers(cd_text)
    assert "schedule" not in _github_triggers(cd_text)
    for job in yaml.safe_load(cd_text)["jobs"].values():
        assert job["if"] == "${{ false }}"
    assert "Azure DevOps is the only CI/CD" in cd_text


def test_azure_ci_runs_only_when_required():
    pipeline = yaml.safe_load(PIPELINE)
    assert "pytest" in PIPELINE
    assert "databricks bundle deploy" not in PIPELINE
    # uv-only toolchain: sync the lockfile, never pip-install requirements.
    assert "uv sync --locked" in PIPELINE
    assert "uv run pytest" in PIPELINE
    assert "python scripts/bundle_validate.py --allow-missing -t develop -t ppe -t prod" in PIPELINE
    assert "continueOnMissing" in PIPELINE
    assert "allowMissingIdentity" in PIPELINE
    assert "ruff" in PIPELINE
    assert "pre-commit run --all-files" in PIPELINE
    assert "python scripts/release_package.py" in PIPELINE
    assert "PublishPipelineArtifact@1" in PIPELINE
    assert "iris-model-wheel" in PIPELINE
    assert "SKIP: no-commit-to-branch" in PIPELINE
    assert "pip install -r requirements" not in PIPELINE
    assert "uv==$(UV_VERSION)" in PIPELINE
    assert "fetchDepth: 1" in PIPELINE
    assert "persistCredentials: false" in PIPELINE
    # Batch collapses superseded pushes. PRs follow feature -> develop -> ppe -> main.
    assert pipeline["trigger"]["batch"] is True
    assert pipeline["trigger"]["branches"]["include"] == ["develop", "ppe", "main"]
    assert "feature" not in str(pipeline["trigger"]["branches"]["include"])
    assert pipeline["pr"]["branches"]["include"] == ["develop", "ppe", "main"]
    assert pipeline["pr"]["drafts"] is False
    assert pipeline["pr"]["autoCancel"] is True
    assert "condition: succeeded()" in PIPELINE
    assert PIPELINE.count("condition: succeededOrFailed()") == 1
    assert "schedules" not in pipeline
    trigger_paths = pipeline["trigger"]["paths"]
    assert "src" in trigger_paths["include"]
    assert "notebooks" in trigger_paths["include"]
    assert "scripts" in trigger_paths["include"]
    assert "azure-pipelines" in trigger_paths["include"]
    assert "uv.lock" in trigger_paths["include"]
    assert "docs" in trigger_paths["exclude"]
    assert trigger_paths["exclude"] == pipeline["pr"]["paths"]["exclude"]
    auth_step = (REPO_ROOT / "azure-pipelines/steps-databricks-command.yml").read_text(
        encoding="utf-8"
    )
    assert "steps-databricks-command.yml" in PIPELINE
    assert "steps-keyvault-secret.yml" in PIPELINE
    assert "sp-iris-develop-client-secret" in PIPELINE
    assert "cd_require_service_principal.py" in auth_step
    assert "ARM_CLIENT_ID: $(ARM_CLIENT_ID)" in auth_step
    assert "DATABRICKS_CLIENT_ID: $(DATABRICKS_CLIENT_ID)" not in PIPELINE
    assert "DATABRICKS_CLIENT_ID: $(DATABRICKS_CLIENT_ID)" not in auth_step
    assert "unset DATABRICKS_TOKEN" in auth_step
    assert "DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)" not in PIPELINE


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
    stage_text = (REPO_ROOT / "azure-pipelines/cd-deploy-stage.yml").read_text(encoding="utf-8")
    assert deploy_text.count("template: azure-pipelines/cd-deploy-stage.yml") == 1
    assert "value: develop" in deploy_text and "value: ppe" in deploy_text
    assert "value: prod" in deploy_text
    assert "group: iris-${{ variables.envSuffix }}" in deploy_text
    assert "environment: iris-${{ variables.envSuffix }}" in stage_text
    assert "group: iris-${{ variables.envSuffix }}" in stage_text
    assert "bundle deploy -t $(envSuffix)" in stage_text

    gh_cd_text = (REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
    assert list(_github_triggers(gh_cd_text)) == ["workflow_dispatch"]
    for job in yaml.safe_load(gh_cd_text)["jobs"].values():
        assert job["if"] == "${{ false }}"
    # CI stays test-only and never calls the CD path.
    assert "databricks bundle deploy" not in PIPELINE
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "databricks bundle deploy" not in ci


def test_cd_databricks_deployment_pipeline_implementation():
    az_cd_text = (REPO_ROOT / "azure-pipelines-cd.yml").read_text(encoding="utf-8")
    az_cd_text += "\n" + (REPO_ROOT / "azure-pipelines/cd-deploy-stage.yml").read_text(
        encoding="utf-8"
    )
    az_cd_text += "\n" + (REPO_ROOT / "azure-pipelines/steps-databricks-cli.yml").read_text(
        encoding="utf-8"
    )
    az_cd_text += "\n" + (REPO_ROOT / "azure-pipelines/steps-databricks-command.yml").read_text(
        encoding="utf-8"
    )
    az_cd_text += "\n" + (REPO_ROOT / "azure-pipelines/steps-keyvault-secret.yml").read_text(
        encoding="utf-8"
    )
    az_cd = yaml.safe_load(az_cd_text)
    assert az_cd["trigger"] == "none"
    assert az_cd["pr"] == "none"
    assert "checkout: self" in az_cd_text
    assert (
        "databricks/setup-cli" in az_cd_text
        or "install.sh" in az_cd_text
        or "databricks_cli_" in az_cd_text
    )
    assert "python scripts/bundle_validate.py --allow-missing -t $(envSuffix)" in az_cd_text
    assert "databricks bundle deploy -t $(envSuffix)" in az_cd_text
    assert "databricks bundle run iris-ml-train -t $(envSuffix)" in az_cd_text
    assert "databricks bundle run iris-ml-infer -t $(envSuffix)" in az_cd_text
    stage_only = (REPO_ROOT / "azure-pipelines/cd-deploy-stage.yml").read_text(encoding="utf-8")
    assert "python scripts/release_package.py" in stage_only
    assert "python scripts/bundle_deploy.py --allow-missing -t $(envSuffix)" in stage_only
    assert _active_command_lines(stage_only, "databricks bundle deploy") == []
    assert _active_command_lines(stage_only, "databricks bundle run") == []
    deploy_script = (REPO_ROOT / "scripts" / "bundle_deploy.py").read_text(encoding="utf-8")
    assert "databricks bundle deploy" in deploy_script
    assert "--auto-approve" in deploy_script
    assert "--force-lock" in deploy_script
    assert "databricks serving-endpoints get iris-species-$(envSuffix)" in az_cd_text
    assert "value: ppe" in az_cd_text and "value: prod" in az_cd_text
    assert "test_serving.py --endpoint iris-species-$(envSuffix)" in az_cd_text

    gh_cd_text = (REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
    gh_cd = yaml.safe_load(gh_cd_text)
    assert "workflow_dispatch" in str(gh_cd)
    assert "databricks/setup-cli@v1.19.0" in gh_cd_text
    assert "pip install databricks-cli" not in gh_cd_text
    assert (
        "python scripts/bundle_validate.py --allow-missing -t develop -t ppe -t prod" in gh_cd_text
    )
    assert "databricks bundle deploy -t" in gh_cd_text
    assert "databricks bundle run iris-ml-train -t" in gh_cd_text
    assert "databricks bundle run iris-ml-infer -t" in gh_cd_text
    assert "python scripts/release_package.py" in gh_cd_text
    assert "python scripts/bundle_deploy.py --allow-missing -t" in gh_cd_text
    assert _active_command_lines(gh_cd_text, "databricks bundle deploy") == []
    assert _active_command_lines(gh_cd_text, "databricks bundle run") == []
    assert "assert_deploy_branch.py" in gh_cd_text
    assert "Build.SourceBranchName'], 'main')" in az_cd_text
    assert "assert_deploy_branch.py --target $(envSuffix)" in az_cd_text
    assert 'test "${{ parameters.confirm }}" = "YES"' in az_cd_text
    assert "refs/heads/develop|refs/heads/ppe|refs/heads/main" in az_cd_text
    assert "lockBehavior: sequential" in az_cd_text
    assert "condition: succeeded()" in az_cd_text
    assert "displayName: Run train job" in az_cd_text
    assert "displayName: Run infer job" in az_cd_text
    deploy_stage = (REPO_ROOT / "azure-pipelines/cd-deploy-stage.yml").read_text(encoding="utf-8")
    assert deploy_stage.count("eq(variables['runMode'], 'train-and-serve')") == 2
    assert gh_cd_text.count("inputs.run_mode == 'train-and-serve'") == 2
    assert "default: Champion" in az_cd_text
    assert "default: serve" in az_cd_text
    assert "train-and-serve" in az_cd_text
    assert "promoteChampion" in az_cd_text
    assert "codeVersion" in az_cd_text
    assert "group: iris-${{ variables.envSuffix }}" in (
        REPO_ROOT / "azure-pipelines-cd.yml"
    ).read_text(encoding="utf-8")
    root_vars = yaml.safe_load((REPO_ROOT / "azure-pipelines-cd.yml").read_text(encoding="utf-8"))[
        "variables"
    ]
    assert all("group" not in item for item in root_vars if isinstance(item, dict))
    assert "test_serving.py --endpoint" in gh_cd_text
    apply = (REPO_ROOT / "scripts" / "apply_served_version.py").read_text(encoding="utf-8")
    assert "serving-endpoints" in apply and '"create"' in apply and '"--no-wait"' in apply
    assert "update-config" in apply
    assert "apply_served_version.py" in az_cd_text
    assert "apply_served_version.py" in gh_cd_text
    assert "cd_require_service_principal.py" in az_cd_text
    assert "cd_require_service_principal.py" in gh_cd_text
    assert "ARM_CLIENT_ID: $(ARM_CLIENT_ID)" in az_cd_text
    assert "DATABRICKS_CLIENT_ID: $(DATABRICKS_CLIENT_ID)" not in az_cd_text
    assert "AzureKeyVault@2" in az_cd_text
    assert "sc-iris-keyvault" in az_cd_text
    assert "sp-iris-${{ variables.envSuffix }}-client-secret" in az_cd_text
    assert "secrets." not in gh_cd_text
    assert "export_keyvault_secret.py" in gh_cd_text
    assert "azure/login@v2" in gh_cd_text
    assert "group: iris-${{ variables.envSuffix }}" in az_cd_text
    assert "unset DATABRICKS_TOKEN" in az_cd_text
    assert "unset DATABRICKS_TOKEN" in gh_cd_text


def _active_command_lines(text: str, phrase: str) -> list[str]:
    """Return uncommented lines that would execute a Databricks command."""
    return [
        line for line in text.splitlines() if phrase in line and not line.strip().startswith("#")
    ]


def test_databricks_bundle_validation_passes():
    import importlib.util
    import shutil

    if not shutil.which("databricks"):
        return
    spec = importlib.util.spec_from_file_location(
        "bundle_validate", REPO_ROOT / "scripts" / "bundle_validate.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.validate_targets(["develop", "ppe", "prod"], allow_missing=True) == 0


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
    assert "iris-species" in doc
    assert "setosa" in doc and "virginica" in doc
