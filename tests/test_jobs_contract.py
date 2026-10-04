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


def _jobs():
    from pathlib import Path

    import yaml

    jobs = {}
    for folder in ("jobs", "tasks"):
        for path in sorted(Path("databricks", folder).glob("*.yml")):
            document = yaml.safe_load(path.read_text())
            for key, value in document["resources"]["jobs"].items():
                current = jobs.setdefault(key, {})
                overlap = set(current) & set(value)
                assert not overlap, f"{path} redefines {key} fields {overlap}"
                current.update(value)
    return jobs


def test_two_jobs_personal_notebook_and_serverless_script():
    from pathlib import Path

    jobs = _jobs()
    assert {
        "iris-train-notebook-personal",
        "iris-train-script-serverless",
    } <= set(jobs)
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
    bundle_text = "".join(path.read_text() for path in sorted(Path("databricks").rglob("*.yml")))
    text = bundle_text + Path("databricks.yml").read_text()
    assert "databricks-token" not in text or "kv-iris-ml-dev-7405" in text
    assert "pywin32" not in Path("requirements-serving.txt").read_text().lower()
    assert "../../requirements-serving.txt" in bundle_text


def test_infer_job_and_train_infer_pipeline():
    from pathlib import Path

    jobs = _jobs()
    assert "iris-infer-script-serverless" in jobs
    assert jobs["iris-infer-script-serverless"]["tags"]["task"] == "infer"
    pipeline = jobs["iris-ml-job-pipeline"]
    assert pipeline["tags"]["task"] == "pipeline"
    keys = [task["task_key"] for task in pipeline["tasks"]]
    assert keys == ["train", "infer"]
    infer_task = next(task for task in pipeline["tasks"] if task["task_key"] == "infer")
    assert infer_task["depends_on"] == [{"task_key": "train"}]
    assert "notebooks/infer.py" in str(infer_task)
    endpoint = Path("databricks/artifacts/iris_endpoint.yml").read_text()
    assert "iris-species-dev" in endpoint
    assert "iris-species-dev" in pipeline.get("description", "")


def test_infer_scores_known_local_rows():
    import importlib.util

    spec = importlib.util.spec_from_file_location("notebooks_infer", "notebooks/infer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = module.infer(module.DEFAULT_MODEL_URI, list(module.KNOWN_ROWS))
    assert [row["prediction"]["species"] for row in results] == list(module.EXPECTED)


def test_infer_param_falls_back_without_dbutils(monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location("notebooks_infer_params", "notebooks/infer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.delenv("MLFLOW_MODEL_URI", raising=False)
    assert module._get_param("MLFLOW_MODEL_URI", module.DEFAULT_MODEL_URI) == (
        module.DEFAULT_MODEL_URI
    )


def test_notebook_model_logging_parity_with_script():
    from pathlib import Path

    text = Path("notebooks/01_train_and_register.ipynb").read_text(encoding="utf-8")
    assert "pip_requirements" in text
    assert "requirements-serving.txt" in text
    assert "signature" in text
    assert "code_paths" in text
