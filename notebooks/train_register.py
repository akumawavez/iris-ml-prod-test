"""Train the iris forest with MLflow tracking and register it for future serving.

Run as a script (Databricks-compatible — no notebook-only magics):

    uv run python notebooks/train_register.py --experiment iris-species --register

Or open ``notebooks/01_train_and_register.ipynb`` for the same code cell-by-cell.

Behaviour:
- Fits a RandomForest on the full iris dataset (same hyperparams as
  ``src/iris_model/train.py`` so the checked-in ``models/iris_species``
  stays reproducible).
- One run logs estimator params (sklearn autolog, model file off), holdout
  metrics, the training dataset, a signature, one input example, a confusion
  matrix, feature importance, tags (including git SHA when the job has one),
  and a single holdout span. The pyfunc is logged once. System-metric
  polling stays off so the serverless task stays short.
- Only registers when ``--register`` is passed AND ``MLFLOW_REGISTERED_MODEL_NAME``
  is set (e.g. ``dbw_iris_ml_dev.develop.iris_species``). Registration sets
  the env alias, version tags, and the model description. Champion moves
  only when a manual CD run says YES.
- Never writes secrets. A laptop run may use ``DATABRICKS_TOKEN`` from
  env. A Databricks job already runs as its service principal, so this
  script does not replace that identity with a personal token.
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
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from iris_model._version import __version__
from iris_model.schema import FEATURES
from iris_model.score import score_forest
from iris_model.train import IrisPyfunc


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
    p.add_argument(
        "--env",
        default=_get_param("MLFLOW_ENV", "develop"),
        help="Environment name written as an MLflow/job tag (develop|ppe|prod).",
    )
    p.add_argument(
        "--alias",
        default=_get_param("MLFLOW_MODEL_ALIAS", ""),
        help="UC alias to point at the new version. Does not move Champion.",
    )
    return p.parse_args()


def git_sha() -> str:
    """Job or CI sha. Empty when the serverless task has no git metadata."""
    for key in ("GIT_SHA", "GITHUB_SHA", "BUILD_SOURCEVERSION"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


def tracking_tags(*, env: str, alias: str, code_version: str, git_sha: str) -> dict[str, str]:
    """Tags a reviewer can filter on. Git SHA is omitted when the job has none."""
    tags = {
        "project": "iris-ml",
        "env": env,
        "stage": env,
        "alias": alias or env,
        "task": "script",
        "compute": "serverless",
        "code_version": code_version,
    }
    if git_sha:
        tags["mlflow.source.git.commit"] = git_sha
    return tags


def version_tags(*, env: str, code_version: str, accuracy: float, git_sha: str) -> dict[str, str]:
    """Tags stored on the Unity Catalog model version, not only the run."""
    tags = {
        "env": env,
        "code_version": code_version,
        "accuracy": f"{accuracy:.6f}",
    }
    if git_sha:
        tags["git_sha"] = git_sha
    return tags


def holdout_metrics(y_true, y_pred, y_train, train_pred) -> dict[str, float]:
    """Cheap holdout numbers. One pass each over train and test, no plots."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "train_accuracy": float(accuracy_score(y_train, train_pred)),
    }


def aliases_for_env(alias: str) -> tuple[str, ...]:
    """The alias this train may move. Champion is a separate manual choice."""
    label = alias.strip()
    if not label:
        return ()
    return (label,)


def set_model_aliases(name: str, version: str, alias: str) -> tuple[str, ...]:
    """Point the requested alias at the registered version."""
    client = mlflow.MlflowClient()
    applied = aliases_for_env(alias)
    for label in applied:
        client.set_registered_model_alias(name, label, version)
        print(f"aliased {name}@{label} -> version {version}")
    return applied


def _job_has_run_identity() -> bool:
    """True when Databricks already authenticated this process as the job identity."""
    return bool(os.getenv("DATABRICKS_RUNTIME_VERSION") or os.getenv("DATABRICKS_JOB_ID"))


def main() -> str:
    args = parse_args()
    if not os.getenv("DATABRICKS_TOKEN") and not _job_has_run_identity():
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
    sha = git_sha()

    try:
        with mlflow.start_run(run_name=f"iris-rf-v{__version__}") as run:
            # Autolog records estimator params and training metrics. The model
            # file is logged once below as the pyfunc the endpoint loads.
            mlflow.sklearn.autolog(
                log_models=False,
                log_datasets=False,
                log_input_examples=False,
                log_model_signatures=False,
                log_post_training_metrics=False,
                silent=True,
            )
            forest.fit(X_train, y_train)
            with mlflow.start_span(name="holdout_predict") as span:
                predicted = forest.predict(X_test)
                span.set_attribute("n_rows", int(predicted.shape[0]))
            train_predicted = forest.predict(X_train)
            metrics = holdout_metrics(y_test, predicted, y_train, train_predicted)
            acc = metrics["accuracy"]
            tags = tracking_tags(
                env=args.env, alias=args.alias, code_version=__version__, git_sha=sha
            )
            tags["llm_style"] = llm_style
            mlflow.set_tags(tags)
            mlflow.log_param("test_size", args.test_size)
            mlflow.log_param("code_version", __version__)
            mlflow.log_metrics(metrics)
            train_frame = pd.DataFrame(X_train, columns=list(FEATURES))
            train_frame["species"] = [bunch.target_names[int(i)] for i in y_train]
            mlflow.log_input(
                mlflow.data.from_pandas(
                    train_frame,
                    source="sklearn.datasets.load_iris",
                    targets="species",
                    name="iris-train",
                ),
                context="training",
            )
            labels = [int(i) for i in range(len(bunch.target_names))]
            mlflow.log_dict(
                {
                    "labels": [str(name) for name in bunch.target_names],
                    "matrix": confusion_matrix(y_test, predicted, labels=labels).tolist(),
                },
                "confusion_matrix.json",
            )
            mlflow.log_table(
                {
                    "feature": list(FEATURES),
                    "importance": [float(v) for v in forest.feature_importances_],
                },
                "feature_importance.json",
            )
            FOREST_STAGING.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(forest, FOREST_STAGING)
            sample_in = pd.DataFrame([dict(zip(FEATURES, X_train[0], strict=True))])
            sample_out = pd.DataFrame(score_forest(forest, sample_in.to_dict(orient="records")))
            sig = mlflow.models.infer_signature(sample_in, sample_out)
            log_kwargs = {
                "name": "model",
                "python_model": IrisPyfunc(),
                "artifacts": {"forest": str(FOREST_STAGING)},
                "signature": sig,
                "input_example": sample_in,
                "code_paths": [str(REPO_ROOT / "src" / "iris_model")],
                "pip_requirements": str(SERVING_REQUIREMENTS),
            }
            if args.register:
                if not args.registered_name:
                    raise SystemExit(
                        "Refusing to register: set MLFLOW_REGISTERED_MODEL_NAME "
                        "(e.g. dbw_iris_ml_dev.develop.iris_species) or pass --registered-name."
                    )
                log_kwargs["registered_model_name"] = args.registered_name
            info = mlflow.pyfunc.log_model(**log_kwargs)
            run_id = run.info.run_id
            print(f"logged run {run_id} accuracy={acc:.4f}")

            if args.register:
                version = str(getattr(info, "registered_model_version", "") or "")
                if not version:
                    mv = mlflow.register_model(
                        model_uri=f"runs:/{run_id}/model", name=args.registered_name
                    )
                    version = str(mv.version)
                    print(f"registered {mv.name} version {version} (status {mv.status})")
                else:
                    print(f"registered {args.registered_name} version {version}")
                set_model_aliases(args.registered_name, version, args.alias or args.env)
                client = mlflow.MlflowClient()
                for key, value in version_tags(
                    env=args.env, code_version=__version__, accuracy=acc, git_sha=sha
                ).items():
                    client.set_model_version_tag(args.registered_name, version, key, value)
                client.update_registered_model(
                    args.registered_name,
                    description=(
                        "Iris random forest. HTTP serving follows the env alias after gated CD."
                    ),
                )
                return version
            return run_id
    finally:
        mlflow.sklearn.autolog(disable=True)


if __name__ == "__main__":
    main()
