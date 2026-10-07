"""The git branch that may deploy each Databricks environment."""

from pathlib import Path

import yaml

from iris_model.promotion import PROMOTION, normalize_branch, stage_for_branch, stage_for_target

ROOT = Path(__file__).resolve().parents[1]


def _load_script():
    import importlib.util

    path = ROOT / "scripts" / "assert_deploy_branch.py"
    spec = importlib.util.spec_from_file_location("assert_deploy_branch", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_promotion_is_develop_then_ppe_then_main():
    assert [stage.git_branch for stage in PROMOTION] == ["develop", "ppe", "main"]
    assert [stage.databricks_target for stage in PROMOTION] == ["develop", "ppe", "prod"]
    assert stage_for_target("prod").git_branch == "main"
    assert stage_for_branch("refs/heads/main").databricks_target == "prod"
    assert all(stage.git_branch != "prod" for stage in PROMOTION)
    assert all(stage.git_branch != "dev" for stage in PROMOTION)


def test_bundle_targets_match_the_promotion_table():
    targets = {}
    for path in sorted((ROOT / "databricks" / "targets").glob("*.yml")):
        targets.update(yaml.safe_load(path.read_text(encoding="utf-8"))["targets"])
    assert set(targets) == {stage.databricks_target for stage in PROMOTION}
    for stage in PROMOTION:
        variables = targets[stage.databricks_target]["variables"]
        assert variables["git_branch"] == stage.git_branch
        assert variables["env"] == stage.databricks_target
        assert variables["env_suffix"] == stage.databricks_target
        assert variables["service_principal_application_id"]
        assert stage.endpoint_name == f"iris-species-{stage.databricks_target}"
    job = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "databricks/jobs").glob("*.yml")
    )
    endpoint = (ROOT / "databricks/artifacts/iris_endpoint.yml").read_text(encoding="utf-8")
    assert "iris-ml-train-${var.env_suffix}" in job
    assert "iris-ml-infer-${var.env_suffix}" in job
    assert "iris-species-${var.env_suffix}" in endpoint
    assert "dbw_iris_ml_dev.${var.env_suffix}.iris_species" in job


def test_deploy_refuses_the_wrong_branch():
    gate = _load_script()
    assert gate.check("prod", "refs/heads/main").startswith("Branch check passed")
    assert gate.check("develop", "develop").startswith("Branch check passed")
    try:
        gate.check("prod", "develop")
    except gate.BranchMismatch as exc:
        assert "main" in str(exc)
        assert "develop" in str(exc)
    else:
        raise AssertionError("expected BranchMismatch")
    assert gate.main(["--target", "ppe", "--branch", "feature/score"]) == 1
    assert gate.main(["--target", "ppe", "--branch", "refs/heads/ppe"]) == 0


def test_cd_calls_the_branch_gate_for_each_target():
    azure = (ROOT / "azure-pipelines-cd.yml").read_text(encoding="utf-8")
    stage_yaml = (ROOT / "azure-pipelines/cd-deploy-stage.yml").read_text(encoding="utf-8")
    github = (ROOT / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
    assert azure.count("template: azure-pipelines/cd-deploy-stage.yml") == 1
    for stage in PROMOTION:
        assert f"value: {stage.databricks_target}" in azure
        if stage.git_branch == stage.databricks_target:
            assert f"'{stage.git_branch}'" in azure
        else:
            assert "'main'" in azure and "value: prod" in azure
    assert "assert_deploy_branch.py --target $(envSuffix)" in stage_yaml
    assert "bundle deploy -t $(envSuffix)" in stage_yaml
    assert "iris-species-$(envSuffix)" in stage_yaml
    assert "assert_deploy_branch.py" in github
    assert "if: ${{ false }}" in github
    assert normalize_branch("refs/heads/ppe") == "ppe"
