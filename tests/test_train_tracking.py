"""Tracking helpers and one local run. No workspace and no register."""

import importlib.util

import mlflow


def _load():
    spec = importlib.util.spec_from_file_location("train_tracking", "notebooks/train_register.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_tags_include_git_sha_only_when_present():
    module = _load()
    tags = module.tracking_tags(env="ppe", alias="", code_version="1.2.3", git_sha="")
    assert tags["alias"] == "ppe"
    assert "mlflow.source.git.commit" not in tags
    tagged = module.tracking_tags(env="ppe", alias="ppe", code_version="1.2.3", git_sha="abc")
    assert tagged["mlflow.source.git.commit"] == "abc"
    versions = module.version_tags(env="prod", code_version="1.2.3", accuracy=0.9, git_sha="abc")
    assert versions["accuracy"] == "0.900000"
    assert versions["git_sha"] == "abc"


def test_one_run_logs_holdout_metrics_and_signature(tmp_path, monkeypatch):
    module = _load()
    uri = f"sqlite:///{tmp_path}/ml.db"
    monkeypatch.setattr(module, "FOREST_STAGING", tmp_path / "forest.joblib")
    monkeypatch.setenv("GIT_SHA", "abc123")
    monkeypatch.setattr(
        module.sys,
        "argv",
        [
            "train_register.py",
            "--experiment",
            "iris-test",
            "--tracking-uri",
            uri,
            "--env",
            "develop",
            "--alias",
            "develop",
        ],
    )
    run_id = module.main()
    client = mlflow.MlflowClient(tracking_uri=uri)
    run = client.get_run(run_id)
    assert run.data.metrics["accuracy"] >= 0.8
    assert "f1_macro" in run.data.metrics
    assert run.data.tags["mlflow.source.git.commit"] == "abc123"
    assert run.data.params["code_version"]
    names = {item.path for item in client.list_artifacts(run_id)}
    assert "confusion_matrix.json" in names
    assert "feature_importance.json" in names
