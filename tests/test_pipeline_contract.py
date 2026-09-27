from pathlib import Path

PIPELINE = Path("azure-pipelines.yml").read_text(encoding="utf-8")


def test_pipeline_runs_pytest_and_does_not_deploy():
    assert "pytest" in PIPELINE
    assert "databricks bundle deploy" not in PIPELINE
    assert "develop" in PIPELINE
