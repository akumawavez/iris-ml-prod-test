from pathlib import Path

import yaml

PIPELINE = Path("azure-pipelines.yml").read_text(encoding="utf-8")
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_runs_pytest_and_does_not_deploy():
    assert "pytest" in PIPELINE
    assert "databricks bundle deploy" not in PIPELINE
    assert "develop" in PIPELINE


def test_bundle_describes_one_develop_endpoint_and_does_not_select_later_targets():
    bundle = yaml.safe_load(Path("databricks.yml").read_text(encoding="utf-8"))
    endpoint = yaml.safe_load(Path("resources/iris_endpoint.yml").read_text(encoding="utf-8"))
    assert bundle["targets"]["develop"]["default"] is True
    assert bundle["targets"]["ppe"]["workspace"]["host"] == ""
    assert bundle["targets"]["prod"]["workspace"]["host"] == ""
    served = endpoint["resources"]["model_serving_endpoints"]["iris_species_dev"]
    assert served["name"] == "iris-species-dev"
    entity = served["config"]["served_entities"][0]
    assert entity["workload_size"] == "Small"
    assert entity["scale_to_zero_enabled"] is True
    assert served["config"]["auto_capture_config"]["enabled"] is True
    text = Path("azure-pipelines.yml").read_text(encoding="utf-8")
    assert "databricks bundle deploy" not in text

def test_github_ci_runs_pytest_only_when_required():
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "pytest" in ci
    assert "databricks bundle deploy" not in ci
    assert "develop" in ci
    # Runs only when required: path-scoped, one ref at a time, never scheduled.
    assert "paths:" in ci
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
    # Batch collapses superseded pushes; PRs stay develop-only; no schedules.
    assert pipeline["trigger"]["batch"] is True
    assert pipeline["pr"]["branches"]["include"] == ["develop"]
    assert "schedules" not in pipeline
    trigger_paths = pipeline["trigger"]["paths"]
    assert "src/*" in trigger_paths["include"]
    assert "docs/*" in trigger_paths["exclude"]


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
