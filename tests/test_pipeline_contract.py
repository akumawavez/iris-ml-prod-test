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
