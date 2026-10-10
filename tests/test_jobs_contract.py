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
    for path in sorted(Path("databricks/jobs").glob("*.yml")):
        document = yaml.safe_load(path.read_text())
        for key, value in document["resources"]["jobs"].items():
            current = jobs.setdefault(key, {})
            overlap = set(current) & set(value)
            assert not overlap, f"{path} redefines {key} fields {overlap}"
            current.update(value)
    return jobs


def test_train_and_infer_are_separate_jobs():
    from pathlib import Path

    jobs = _jobs()
    assert set(jobs) == {"iris-ml-train", "iris-ml-infer"}
    bundle_text = "".join(path.read_text() for path in sorted(Path("databricks").rglob("*.yml")))
    text = bundle_text + Path("databricks.yml").read_text()
    assert "iris-train-notebook-personal" not in text
    assert "iris-train-script-serverless" not in text
    assert "iris-infer-script-serverless" not in text
    assert "personal_compute_id" not in text
    assert "databricks-token" not in text or "kv-iris-ml-dev-7405" in text
    assert "pywin32" not in Path("requirements-serving.txt").read_text().lower()
    assert "../../dist/*.whl" in bundle_text
    assert "uv build --wheel" in text
    assert "type: whl" in text
    assert "-r ../../requirements-serving.txt" not in bundle_text
    train = Path("notebooks/train_register.py").read_text(encoding="utf-8")
    infer = Path("notebooks/infer.py").read_text(encoding="utf-8")
    assert "sys.path.insert" not in train
    assert "sys.path.insert" not in infer


def test_infer_job_and_train_job_are_separate():
    from pathlib import Path

    jobs = _jobs()
    train = jobs["iris-ml-train"]
    infer = jobs["iris-ml-infer"]
    assert train["name"] == "iris-ml-train-${var.env_suffix}"
    assert infer["name"] == "iris-ml-infer-${var.env_suffix}"
    for job in (train, infer):
        assert job["run_as"]["service_principal_name"] == "${var.service_principal_application_id}"
        assert job["tags"]["alias"] == "${var.env_suffix}"
        assert "depends_on" not in job["tasks"][0]
        assert job["environments"][0]["spec"]["client"] == "4"
        assert job["max_concurrent_runs"] == 1
        assert job["queue"]["enabled"] is False
    assert train["timeout_seconds"] == 1200
    assert infer["timeout_seconds"] == 600
    assert [task["task_key"] for task in train["tasks"]] == ["train"]
    assert [task["task_key"] for task in infer["tasks"]] == ["infer"]
    assert train["tags"]["task"] == "train"
    assert infer["tags"]["task"] == "infer"
    assert "notebooks/train_register.py" in str(train["tasks"][0])
    assert "--register" in train["tasks"][0]["spark_python_task"]["parameters"]
    assert "notebooks/infer.py" in str(infer["tasks"][0])
    assert "@${var.env_suffix}" in str(infer)
    endpoint = Path("databricks/artifacts/iris_endpoint.yml").read_text()
    assert "iris-species-${var.env_suffix}" in endpoint
    assert "iris-ml-infer-${var.env_suffix}" in train.get("description", "")
    assert "iris-ml-train-${var.env_suffix}" in infer.get("description", "")


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


def test_train_aliases_include_env_and_champion():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "notebooks_train_aliases", "notebooks/train_register.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.aliases_for_env("ppe") == ("ppe",)
    assert module.aliases_for_env("Champion") == ("Champion",)
    assert module.aliases_for_env("") == ()


def test_infer_falls_back_to_local_model_when_registered_model_is_gone(monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location("notebooks_infer_fallback", "notebooks/infer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def missing(_model_uri: str) -> str:
        raise SystemExit("No registered versions for dbw_iris_ml_dev.develop.iris_species")

    monkeypatch.setattr(module, "resolve_model_uri", missing)
    results = module.infer(
        "models:/dbw_iris_ml_dev.develop.iris_species@develop",
        list(module.KNOWN_ROWS),
    )
    assert [row["prediction"]["species"] for row in results] == list(module.EXPECTED)


def test_infer_apply_alias_on_versionless_uri():
    import importlib.util

    spec = importlib.util.spec_from_file_location("notebooks_infer_alias", "notebooks/infer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (
        module.apply_alias("models:/dbw_iris_ml_dev.ppe.iris_species", "ppe")
        == "models:/dbw_iris_ml_dev.ppe.iris_species@ppe"
    )
    assert (
        module.apply_alias("models:/dbw_iris_ml_dev.ppe.iris_species@ppe", "prod")
        == "models:/dbw_iris_ml_dev.ppe.iris_species@ppe"
    )


def test_targets_share_host_and_suffix_names_by_env():
    from pathlib import Path

    import yaml

    targets = {}
    for path in sorted(Path("databricks/targets").glob("*.yml")):
        targets.update(yaml.safe_load(path.read_text())["targets"])
    assert set(targets) == {"develop", "ppe", "prod"}
    for name in ("develop", "ppe", "prod"):
        target = targets[name]
        assert target["workspace"]["host"] == ("https://adb-7405619226406985.5.azuredatabricks.net")
        assert target["variables"]["env"] == name
        assert target["variables"]["git_branch"] == ("main" if name == "prod" else name)
        assert target["variables"]["env_suffix"] == name


def test_notebook_model_logging_parity_with_script():
    from pathlib import Path

    text = Path("notebooks/01_train_and_register.ipynb").read_text(encoding="utf-8")
    assert "pip_requirements" in text
    assert "requirements-serving.txt" in text
    assert "signature" in text
    assert "code_paths" in text
    assert "MLFLOW_MODEL_ALIAS" in text
    assert "set_registered_model_alias" in text


def test_postman_collection_parses_with_two_scored_requests():
    import json
    from pathlib import Path

    col = json.loads(
        Path("docs/postman/iris-dev.postman_collection.json").read_text(encoding="utf-8")
    )
    env = json.loads(
        Path("docs/postman/iris-dev.postman_environment.json").read_text(encoding="utf-8")
    )
    names = [r["name"] for r in col["item"]]
    assert names == ["score-setosa", "score-virginica"]
    assert {v["key"] for v in env["values"]} >= {"endpoint_url", "databricks_token"}
    token = next(v for v in env["values"] if v["key"] == "databricks_token")
    assert token["value"] == ""
    setosa, virginica = col["item"]
    assert setosa["request"]["method"] == "POST"
    assert virginica["request"]["method"] == "POST"
    setosa_url = setosa["request"]["url"]
    raw = setosa_url if isinstance(setosa_url, str) else setosa_url.get("raw", "")
    assert "{{endpoint_url}}" in raw
    assert "invocations" in raw
    setosa_body = json.loads(setosa["request"]["body"]["raw"])
    virginica_body = json.loads(virginica["request"]["body"]["raw"])
    assert setosa_body["dataframe_records"][0] == {
        "sepal_length_cm": 5.1,
        "sepal_width_cm": 3.5,
        "petal_length_cm": 1.4,
        "petal_width_cm": 0.2,
    }
    assert virginica_body["dataframe_records"][0] == {
        "sepal_length_cm": 6.3,
        "sepal_width_cm": 2.9,
        "petal_length_cm": 5.6,
        "petal_width_cm": 1.8,
    }
    setosa_tests = "\n".join(setosa.get("event", [{}])[0].get("script", {}).get("exec", []))
    virginica_tests = "\n".join(virginica.get("event", [{}])[0].get("script", {}).get("exec", []))
    assert "prediction.species" in setosa_tests and "setosa" in setosa_tests
    assert "prediction.species" in virginica_tests and "virginica" in virginica_tests
    assert "layman" in setosa_tests and "layman" in virginica_tests
