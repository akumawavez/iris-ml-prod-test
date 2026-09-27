from pathlib import Path
import yaml

PIPELINE = Path("azure-pipelines.yml").read_text(encoding="utf-8")


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
