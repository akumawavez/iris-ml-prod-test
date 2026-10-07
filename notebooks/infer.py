"""Batch-infer known iris rows against a local path or registered model.

Run as a script (Databricks-compatible — no notebook-only magics):

    uv run python notebooks/infer.py
    uv run python notebooks/infer.py --model-uri models:/dbw_iris_ml_dev.develop.iris_species

Behaviour:
- Scores the committed setosa and virginica rows.
- Loads a filesystem MLflow model by default (``models/iris_species``).
- On Databricks, pass ``--model-uri models:/<catalog.schema.model>`` to score
  the latest Unity Catalog version after the train task registers it.
- Fails the job if predicted species are not setosa then virginica.
- Never writes secrets. Connection values come from env / ``.env``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import mlflow
import pandas as pd

from iris_model.schema import FEATURES, validate_rows
from iris_model.score import score_model

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _repo_root() -> Path:
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "src" / "iris_model").is_dir():
            return candidate
    bundled = Path("/Workspace/Shared/.bundle/iris-ml-prod-test/develop/files")
    if (bundled / "src" / "iris_model").is_dir():
        return bundled
    return cwd


REPO_ROOT = _repo_root()
try:
    from dotenv import load_dotenv
except ImportError:  # the job wheel does not include python-dotenv

    def load_dotenv(*_args, **_kwargs):
        return False


load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT.parent / ".env", override=False)

DEFAULT_MODEL_URI = "models/iris_species"
SETOSA = {
    "sepal_length_cm": 5.1,
    "sepal_width_cm": 3.5,
    "petal_length_cm": 1.4,
    "petal_width_cm": 0.2,
}
VIRGINICA = {
    "sepal_length_cm": 6.3,
    "sepal_width_cm": 2.9,
    "petal_length_cm": 5.6,
    "petal_width_cm": 1.8,
}
KNOWN_ROWS = (SETOSA, VIRGINICA)
EXPECTED = ("setosa", "virginica")


def _get_param(name: str, default: str) -> str:
    """Read a Databricks widget, else env, else default. No secrets here."""
    try:
        value = dbutils.widgets.get(name)  # type: ignore[name-defined] # noqa: F821
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def _get_secret(scope: str, key: str, env_fallback: str = "") -> str:
    """Read a Databricks secret scope, else env, else fallback. Values never logged."""
    try:
        return dbutils.secrets.get(scope=scope, key=key)  # type: ignore[name-defined] # noqa: F821
    except Exception:
        return os.getenv(key, env_fallback)


def _needs_latest(model_uri: str) -> bool:
    if not model_uri.startswith("models:/"):
        return False
    body = model_uri[len("models:/") :]
    if "@" in body:
        return False
    tail = body.rsplit("/", 1)[-1]
    return tail == "latest" or not tail.isdigit()


def resolve_model_uri(model_uri: str) -> str:
    """Use a local folder when it exists; otherwise resolve UC 'latest'."""
    path = Path(model_uri)
    if not path.is_absolute():
        path = REPO_ROOT / model_uri
    if path.exists():
        return str(path)
    if _needs_latest(model_uri):
        body = model_uri[len("models:/") :]
        name = body.rsplit("/", 1)[0] if body.endswith("/latest") else body
        client = mlflow.MlflowClient()
        versions = list(client.search_model_versions(f"name='{name}'"))
        if not versions:
            raise SystemExit(f"No registered versions for {name}")
        latest = max(versions, key=lambda version: int(version.version))
        return f"models:/{name}/{latest.version}"
    return model_uri


def infer(model_uri: str, rows: list[dict]) -> list[dict]:
    """Score rows with a local MLflow path or a models:/ URI."""
    validate_rows(rows)
    resolved = resolve_model_uri(model_uri)
    if Path(resolved).exists():
        return score_model(Path(resolved), rows)
    loaded = mlflow.pyfunc.load_model(resolved)
    frame = pd.DataFrame(rows).loc[:, list(FEATURES)]
    raw = loaded.predict(frame)
    if isinstance(raw, pd.DataFrame):
        raw = raw.to_dict(orient="records")
    return list(raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch-infer known iris rows.")
    parser.add_argument(
        "--model-uri",
        default=_get_param("MLFLOW_MODEL_URI", DEFAULT_MODEL_URI),
        help="Local MLflow folder or models:/catalog.schema.model[/version].",
    )
    parser.add_argument(
        "--tracking-uri",
        default=_get_param("MLFLOW_TRACKING_URI", "sqlite:///mlruns.db"),
    )
    parser.add_argument(
        "--alias",
        default=_get_param("MLFLOW_MODEL_ALIAS", ""),
        help="If model-uri has no version, load models:/name@alias.",
    )
    return parser.parse_args()


def apply_alias(model_uri: str, alias: str) -> str:
    """Attach @alias when the URI is a versionless models:/ name."""
    if not alias or not model_uri.startswith("models:/") or "@" in model_uri:
        return model_uri
    if _needs_latest(model_uri):
        body = model_uri[len("models:/") :].removesuffix("/latest")
        return f"models:/{body}@{alias}"
    return model_uri


def _job_has_run_identity() -> bool:
    """True when Databricks already authenticated this process as the job identity."""
    return bool(os.getenv("DATABRICKS_RUNTIME_VERSION") or os.getenv("DATABRICKS_JOB_ID"))


def main() -> list[dict]:
    args = parse_args()
    if not os.getenv("DATABRICKS_TOKEN") and not _job_has_run_identity():
        token = _get_secret("kv-iris-ml-dev-7405", "databricks-token")
        if token:
            os.environ["DATABRICKS_TOKEN"] = token
    mlflow.set_tracking_uri(args.tracking_uri)
    model_uri = apply_alias(args.model_uri, args.alias)
    results = infer(model_uri, list(KNOWN_ROWS))
    species = tuple(row["prediction"]["species"] for row in results)
    print(json.dumps(results, indent=2))
    if species != EXPECTED:
        raise SystemExit(f"unexpected species {species}; expected {EXPECTED}")
    print(f"batch infer OK species={list(species)} model={resolve_model_uri(model_uri)}")
    return results


if __name__ == "__main__":
    main()
