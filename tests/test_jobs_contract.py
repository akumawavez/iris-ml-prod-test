def test_param_falls_back_without_dbutils(monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "notebooks_train_register", "notebooks/train_register.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.delenv("LLM_EXPLANATION_STYLE", raising=False)
    assert m._get_param("LLM_EXPLANATION_STYLE", "concise") == "concise"


def test_unknown_llm_style_falls_back_to_concise():
    from iris_model.narratives import explain_layman

    assert explain_layman("nonsense", "setosa", "petal_length_cm", 0.9) == explain_layman(
        "concise", "setosa", "petal_length_cm", 0.9
    )


def test_secret_falls_back_without_dbutils(monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "notebooks_train_register", "notebooks/train_register.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.delenv("databricks-token", raising=False)
    assert m._get_secret("kv-iris-ml-dev-7405", "databricks-token") == ""


def test_two_jobs_personal_notebook_and_serverless_script():
    from pathlib import Path

    import yaml

    jobs = yaml.safe_load(Path("resources/jobs.yml").read_text())["resources"]["jobs"]
    assert set(jobs) == {"iris-train-notebook-personal", "iris-train-script-serverless"}
    assert jobs["iris-train-notebook-personal"]["tags"] == {
        "project": "iris-ml",
        "env": "develop",
        "task": "notebook",
        "compute": "personal",
        "managed-by": "dab",
        "owner": "${var.owner}",
    }
    assert "existing_cluster_id" in str(
        jobs["iris-train-notebook-personal"]
    ) and "${var.personal_compute_id}" in str(jobs["iris-train-notebook-personal"])
    assert jobs["iris-train-script-serverless"]["tags"]["compute"] == "serverless"
    text = Path("resources/jobs.yml").read_text() + Path("databricks.yml").read_text()
    assert "databricks-token" not in text or "kv-iris-ml-dev-7405" in text
    assert "pywin32" not in Path("requirements-serving.txt").read_text().lower()


def test_notebook_model_logging_parity_with_script():
    from pathlib import Path

    text = Path("notebooks/01_train_and_register.ipynb").read_text(encoding="utf-8")
    assert "pip_requirements" in text
    assert "requirements-serving.txt" in text
    assert "signature" in text
    assert "code_paths" in text
