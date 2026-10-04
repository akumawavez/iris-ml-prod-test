"""Train the iris forest with MLflow tracking and register it for future serving.

Run as a script (Databricks-compatible — no notebook-only magics):

    uv run python notebooks/train_register.py --experiment iris-species --register

Or open ``notebooks/01_train_and_register.ipynb`` for the same code cell-by-cell.

Behaviour:
- Fits a RandomForest on the full iris dataset (same hyperparams as
  ``src/iris_model/train.py`` so the checked-in ``models/iris_species``
  stays reproducible).
- Logs params, accuracy, and the pyfunc wrapper to MLflow Tracking.
- Only registers when ``--register`` is passed AND ``MLFLOW_REGISTERED_MODEL_NAME``
  is set (e.g. ``dev.iris_prod.iris_species`` for Unity Catalog).
- Never writes secrets. Connection values come from env / ``.env`` (see
  ``.env.example``): ``MLFLOW_TRACKING_URI``, ``DATABRICKS_HOST``,
  ``DATABRICKS_TOKEN``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import joblib
import mlflow
import mlflow.pyfunc
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


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
sys.path.insert(0, str(REPO_ROOT / "src"))
try:
    from dotenv import load_dotenv
except ImportError:  # serverless job env has serving pins only
    def load_dotenv(*_args, **_kwargs):
        return False

from iris_model._version import __version__  # noqa: E402
from iris_model.schema import FEATURES  # noqa: E402
from iris_model.score import score_forest  # noqa: E402
from iris_model.train import IrisPyfunc  # noqa: E402

load_dotenv()  # local .env; ignored in git. Databricks uses its own env/secrets.
FOREST_STAGING = REPO_ROOT / "models" / "forest.joblib"
SERVING_REQUIREMENTS = REPO_ROOT / "requirements-serving.txt"


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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train + optionally register iris model.")
    p.add_argument("--experiment", default=_get_param("MLFLOW_EXPERIMENT_NAME", "iris-species"))
    p.add_argument(
        "--tracking-uri", default=_get_param("MLFLOW_TRACKING_URI", "sqlite:///mlruns.db")
    )
    p.add_argument("--register", action="store_true", help="Register model after logging.")
    p.add_argument(
        "--registered-name",
        default=_get_param("MLFLOW_REGISTERED_MODEL_NAME", ""),
        help="e.g. dev.iris_prod.iris_species (Unity Catalog) or iris_species (WS registry).",
    )
    p.add_argument("--n-estimators", type=int, default=100)
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--test-size", type=float, default=0.2)
    return p.parse_args()


def main() -> str:
    args = parse_args()
    if not os.getenv("DATABRICKS_TOKEN"):
        token = _get_secret("kv-iris-ml-dev-7405", "databricks-token")
        if token:
            os.environ["DATABRICKS_TOKEN"] = token
    llm_style = _get_param("LLM_EXPLANATION_STYLE", "concise")
    if llm_style not in ("concise", "eli5", "verbose"):
        llm_style = "concise"
    mlflow.set_tracking_uri(args.tracking_uri)

    # Databricks MLflow requires an absolute workspace path for experiment names.
    # Auto-prefix with /Users/<current-user>/ when targeting Databricks and the
    # name is not already an absolute path.
    experiment_name = args.experiment
    tracking_uri = args.tracking_uri or os.getenv("MLFLOW_TRACKING_URI", "")
    if tracking_uri in ("databricks", "") or tracking_uri.startswith("https://"):
        if not experiment_name.startswith("/"):
            import subprocess  # noqa: PLC0415

            try:
                result = subprocess.run(
                    ["databricks", "current-user", "me", "--output", "json"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                import json  # noqa: PLC0415

                user_name = json.loads(result.stdout).get("userName", "")
            except Exception:
                user_name = os.getenv("DATABRICKS_USERNAME", "")
            if user_name:
                experiment_name = f"/Users/{user_name}/{experiment_name}"
            else:
                experiment_name = f"/Shared/{experiment_name}"
    mlflow.set_experiment(experiment_name)

    bunch = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        bunch.data, bunch.target, test_size=args.test_size, random_state=args.random_state
    )
    forest = RandomForestClassifier(n_estimators=args.n_estimators, random_state=args.random_state)
    forest.fit(X_train, y_train)
    acc = float(accuracy_score(y_test, forest.predict(X_test)))

    FOREST_STAGING.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(forest, FOREST_STAGING)

    with mlflow.start_run(run_name=f"iris-rf-v{__version__}") as run:
        mlflow.set_tags(
            {
                "project": "iris-ml",
                "env": "develop",
                "task": "script",
                "compute": "serverless",
                "code_version": __version__,
                "llm_style": llm_style,
            }
        )
        mlflow.log_param("n_estimators", args.n_estimators)
        mlflow.log_param("random_state", args.random_state)
        mlflow.log_param("test_size", args.test_size)
        mlflow.log_param("code_version", __version__)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_table(
            {
                "feature": list(FEATURES),
                "importance": [float(v) for v in forest.feature_importances_],
            },
            "feature_importance.json",
        )
        sample_in = pd.DataFrame([dict(zip(FEATURES, X_train[0], strict=True))])
        sample_out = pd.DataFrame(score_forest(forest, sample_in.to_dict(orient="records")))
        sig = mlflow.models.infer_signature(sample_in, sample_out)
        mlflow.pyfunc.log_model(
            name="model",
            python_model=IrisPyfunc(),
            artifacts={"forest": str(FOREST_STAGING)},
            signature=sig,
            code_paths=[str(REPO_ROOT / "src" / "iris_model")],
            pip_requirements=str(SERVING_REQUIREMENTS),
        )
        run_id = run.info.run_id
        print(f"logged run {run_id} accuracy={acc:.4f}")

        if args.register:
            if not args.registered_name:
                raise SystemExit(
                    "Refusing to register: set MLFLOW_REGISTERED_MODEL_NAME "
                    "(e.g. dev.iris_prod.iris_species) or pass --registered-name."
                )
            mv = mlflow.register_model(model_uri=f"runs:/{run_id}/model", name=args.registered_name)
            print(f"registered {mv.name} version {mv.version} (status {mv.status})")
            return mv.version
    return run_id


if __name__ == "__main__":
    main()
