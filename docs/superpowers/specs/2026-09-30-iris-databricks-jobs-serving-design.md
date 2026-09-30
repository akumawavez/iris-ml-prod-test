# Spec: Iris Databricks jobs + serving (develop)

## Objective

Teach the Databricks production path on the live develop workspace without
forking model logic: one notebook and one Python script do the same
train → MLflow-log → register flow, scheduled as two Databricks Jobs on
different computes, served by the existing serverless endpoint. Every
config value arrives via env vars, secrets arrive via Key Vault-backed
secret scope read through `dbutils`, and tags are set on the bundle, both
jobs, and every MLflow run so each surface is explorable in the UI.

The person using this repo is learning Databricks by building it: feature
branch, pull request, `develop`, DAB `validate` now, `deploy`/`run` only
after written cost approval. No paid action runs as part of this spec's
implementation.

Decisions already locked by the human partner (2026-09-30):

- Keep live names: workspace `adb-7405619226406985.5`, Unity Catalog model
  `dbw_iris_ml_dev.develop.iris_species`, endpoint `iris-species-dev`,
  secret scope backed by `kv-iris-ml-dev-7405`.
- LLM explanation = local template only. Env var `LLM_EXPLANATION_STYLE`
  (`concise` | `eli5` | `verbose`) switches wording inside
  `src/iris_model/narratives.py`. No network call, no key, no cost.
- Approach A (jobs-only on top of existing code). No full folder
  restructure; no logic fork.

Success for the work this spec allows:

- The same notebook runs three ways: interactive on a personal compute,
  as Job-A (notebook task, personal compute), and the same logic runs as
  Job-B (Python-file task, serverless compute).
- Both jobs log to Databricks MLflow tracking, register versions of the
  same Unity Catalog model, and carry identical tag keys.
- `databricks bundle validate -t develop` passes. No deploy, no run, no
  Azure create happens during implementation.
- A Postman collection scores the endpoint for setosa and virginica rows.

## Tech stack

- Python 3.11+ (repo pins `>=3.11`; serving pins are the conservative set
  in `requirements-serving.txt`: `cloudpickle==3.0.0`, `joblib==1.4.2`,
  `mlflow==3.3.2`, `numpy==1.26.4`, `pandas==2.2.3`,
  `scikit-learn==1.5.2`, `scipy==1.13.1`, `shap==0.46.0`).
- scikit-learn `RandomForestClassifier(n_estimators=100, random_state=42)`
  on all 150 `load_iris` rows (teaching fit, no holdout for the committed
  artifact; the tracking script keeps its 80/20 split for the logged
  accuracy metric only).
- MLflow Pyfunc served through `src/iris_model/train.py:IrisPyfunc`,
  which delegates every row to `score_forest`.
- Databricks Asset Bundles for jobs + endpoint description; Jobs API
  (notebook task + Python-file task); Model Serving (serverless CPU).
- `dbutils.widgets` + `dbutils.secrets` with `os.getenv` fallback so every
  notebook/script also runs under Jupyter and plain `uv run`.
- uv as the single dependency source: `uv pip compile` produces
  `requirements-serving.txt`; local and CI consume `uv sync` / `uv run`;
  Databricks installs the compiled file (`%pip install -r` / job
  `environment.dependencies`). uv itself is not installed on Databricks
  runtimes.
- pytest + ruff (existing gates stay green). Azure DevOps Pipelines for CI
  (test + validate) and a human-gated CD stage. Postman for the smoke test.

## Commands (safe to run during implementation)

From the repository root:

```text
uv sync --extra dev
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python notebooks/train_register.py
databricks bundle validate -t develop
```

Explicitly NOT part of implementation (each waits for written cost
approval in a PR comment on `docs/cost-sheet.md`):

```text
databricks bundle deploy -t develop
databricks bundle run -t develop iris-train-notebook-personal
databricks bundle run -t develop iris-train-script-serverless
uv run python notebooks/train_register.py --register
```

`--register` without approval would create UC model version 6 against the
live workspace. The code supports it; this spec forbids running it now.

## Project structure (evolution, not rewrite)

```text
src/iris_model/__init__.py          package marker (unchanged)
src/iris_model/schema.py            FEATURES, SPECIES, validate_rows (unchanged)
src/iris_model/narratives.py        + LLM_EXPLANATION_STYLE switch (local template)
src/iris_model/train.py             IrisPyfunc + pip_requirements="requirements-serving.txt" (unchanged)
src/iris_model/score.py             score_model + score_forest (unchanged)
notebooks/train_register.py         script job source: widgets/env/tags/uv-install header (extended, logic reused)
notebooks/01_train_and_register.ipynb  notebook job source + interactive personal-compute path (extended, logic reused)
resources/iris_endpoint.yml         iris-species-dev, entity_version bumped 5 -> 6 only after v6 exists
resources/jobs.yml                  NEW: the two jobs below
databricks.yml                      + variables personal_compute_id / registered_model_name, includes resources/*.yml
docs/postman/                       NEW: iris-dev.postman_collection.json + iris-dev.postman_environment.json
tests/test_jobs_contract.py         NEW: parses databricks.yml + resources/jobs.yml, asserts the Success criteria
requirements-serving.txt            single compiled serving set (unchanged content unless uv recompile is needed)
```

No new top-level framework directories. A full `features/` / `training/`
/ `serving/` split is explicitly out of scope (see Out of scope).

## Code style

Names stay lowercase with underscores. `FEATURES` order is unchanged:

```python
FEATURES = (
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
)
```

Databricks wrappers follow one pattern so local runs never break:

```python
def _get_param(name: str, default: str) -> str:
    """Read a Databricks widget, else env, else default. No secrets here."""
    try:
        value = dbutils.widgets.get(name)  # type: ignore[name-defined]
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)
```

Secrets follow one pattern (scope name committed, secret values never):

```python
def _get_secret(scope: str, key: str, env_fallback: str = "") -> str:
    try:
        return dbutils.secrets.get(scope=scope, key=key)  # type: ignore[name-defined]
    except Exception:
        return os.getenv(key, env_fallback)
```

Public functions keep one-line docstrings. Wrappers log; they do not refit
with different hyperparameters.

## Response contract (unchanged)

`score_model` and the served `IrisPyfunc.predict` return one object per row
with `input`, `prediction{species, probabilities}`, `shap{calculation,
layman}`, `feature_importance{calculation, layman}` per
`docs/superpowers/specs/2026-09-27-iris-develop-serving-design.md`. The
`LLM_EXPLANATION_STYLE` switch only selects among pre-written layman
templates (`concise` = shortest, `eli5` = analogy, `verbose` = full
calculation walk-through). It never changes probabilities, SHAP values, or
importances, and `json.dumps` on the list must still succeed.

## Model fitting and registration (v6 plan, not executed here)

- Algorithm and data are unchanged: 100 trees, `random_state=42`.
- The serving container is built from `requirements-serving.txt` only.
  `requirements.txt` (which contains Windows-only `pywin32`) is never
  referenced by `pip_requirements`.
- Version 5 (current endpoint target) carries the bad requirements and
  stays `UPDATE_FAILED`. The fix is a new version 6 registered from the
  clean requirements, then `entity_version: "6"`. Editing YAML alone does
  not fix serving.
- Registration command (gated, do not run now):

```text
uv run python notebooks/train_register.py --register
```

with env `MLFLOW_REGISTERED_MODEL_NAME=dbw_iris_ml_dev.develop.iris_species`
and `MLFLOW_TRACKING_URI=databricks`.

Known rows the served model must classify correctly:

| Species | sepal_length_cm | sepal_width_cm | petal_length_cm | petal_width_cm |
|---|---|---:|---:|---:|
| setosa | 5.1 | 3.5 | 1.4 | 0.2 |
| virginica | 6.3 | 2.9 | 5.6 | 1.8 |

## Jobs

Defined in `resources/jobs.yml`. Both jobs share env, tags, and the
`iris-species` experiment. Personal compute identity is a deploy-time
variable, never committed.

```yaml
variables:
  personal_compute_id:
    description: Existing personal-compute resource ID; passed via --var at deploy time.
    default: ""
  registered_model_name:
    description: Unity Catalog model for registration.
    default: dbw_iris_ml_dev.develop.iris_species
  experiment_name:
    description: MLflow experiment name (auto-prefixed with /Users/<you>/ on Databricks).
    default: iris-species
  owner:
    description: Short owner name applied as a tag only (no auth semantics).
    default: iris-learn
```

Job-A `iris-train-notebook-personal`:

- `notebook_task.notebook_path: ../notebooks/01_train_and_register.ipynb`
  (deployed notebook source, same file runnable interactively).
- Compute: `existing_cluster_id: ${var.personal_compute_id}`.
- `notebook_task.base_parameters`: `MLFLOW_EXPERIMENT_NAME`,
  `MLFLOW_REGISTERED_MODEL_NAME: ${var.registered_model_name}`,
  `LLM_EXPLANATION_STYLE`.
- `tags`: `project: iris-ml`, `env: develop`, `task: notebook`,
  `compute: personal`, `managed-by: dab`, `owner: ${var.owner}`.
- Libraries: none extra (personal compute already carries the project
  env); notebook header runs `%pip install -r requirements-serving.txt`
  only when `import sklearn` fails, so interactive runs stay fast.

Job-B `iris-train-script-serverless`:

- `spark_python_task.python_file: ../notebooks/train_register.py`,
  `parameters: ["--experiment", "${var.experiment_name}", ...]` mirroring
  the same three env vars.
- Compute: serverless (`environments: [{environment_key: default,
  spec: {client: "2", dependencies:
  ["requirements-serving.txt"]}}]`), no cluster ID.
- Same `tags` with `task: script`, `compute: serverless`, `owner: ${var.owner}`.

Local-run story (all three supported, none needs a code fork):

1. Laptop/Jupyter: `uv run python notebooks/train_register.py`
   (tracking `sqlite:///mlruns.db`, log-only).
2. Interactive Databricks: open the deployed notebook on the personal
   compute, fill widgets (or accept env defaults), Run All.
3. Scheduled/gated: Jobs UI Run Now with parameter overrides, or (after
   approval) `databricks bundle run -t develop <job-name>`.

## Env vars, secrets, tags, uv

| Name | Default | Set where |
|---|---|---|
| `MLFLOW_TRACKING_URI` | `sqlite:///mlruns.db` locally, `databricks` in both jobs | `base_parameters` (Job-A notebook) / `--tracking-uri` argv (Job-B); plain env only for local runs — `environment_vars` exists on neither Job nor Task structs |
| `MLFLOW_EXPERIMENT_NAME` | `iris-species` (script auto-prefixes `/Users/<you>/` on Databricks) | widget + env |
| `MLFLOW_REGISTERED_MODEL_NAME` | `""` (log-only) locally; `${var.registered_model_name}` in jobs | widget + env |
| `LLM_EXPLANATION_STYLE` | `concise` | widget + env |
| `DATABRICKS_HOST` | empty | local `.env` only; jobs use the bundle's authenticated workspace |
| `DATABRICKS_TOKEN` | empty | local `.env`; Key Vault → secret scope at runtime |

Secret scope: `kv-iris-ml-dev-7405` (backed by `kv-iris-ml-dev-7405`).
Scope and key names (`databricks-token`) are committed; values never are.
`tests/test_jobs_contract.py` fails the build if any secret-looking value
appears in YAML.

MLflow tags on every run (both paths call `mlflow.set_tags`):

```text
project=iris-ml env=develop code_version=<__version__>
task=notebook|script compute=personal|serverless llm_style=<style>
```

Per-job six tag keys (`project`, `env`, `task`, `compute`, `managed-by`,
`owner`) are the tagging surface. Bundle-wide tag inheritance is unsupported
by CLI v1.18.0 (verified against `databricks bundle schema` — `tags` exists
on Job resources, not at bundle root); `cost-center: learning` is recorded
as a limitation, not applied.

uv story (the honest version): `uv pip compile pyproject.toml -o
requirements-serving.txt` is the only producer of the serving pin set.
Databricks installs that file. `uv sync --extra dev` + `uv run` remain
the local/CI path. No `uv` binary is installed on Databricks.

## Data flow

```text
feature/databricks-jobs-serving
  -> PR into develop: pytest + ruff + bundle validate (CI, no deploy)
  -> merge after human approval
      -> (later, approved) bundle deploy -t develop
      -> Job-A on personal compute AND Job-B on serverless log + register v6
      -> endpoint YAML bumped 5 -> 6, redeployed, serves v6
      -> Postman scores v6 for setosa + virginica

notebook interactive run (any time, no deploy):
  open notebook -> personal compute -> widgets/env -> Databricks MLflow run
```

## Testing strategy

- `uv run pytest -q` stays green; `uv run ruff check .` stays green.
- Existing `tests/test_score.py` and `tests/test_pipeline_contract.py`
  are untouched and must pass.
- New `tests/test_jobs_contract.py` parses YAML as text + YAML and
  asserts: exactly two jobs; Job-A references
  `${var.personal_compute_id}` and a notebook path; Job-B is serverless
  with a Python-file path; both jobs carry the six tag keys; both set the
  three `MLFLOW_*`/`LLM_*` params; no `databricks bundle deploy` string in
  CI YAML; no secret values in any YAML.
- Postman collection is data, not a test gate: two requests (setosa,
  virginica) asserting `prediction.species` and both `layman` strings.
- Anything needing the network, a subscription, or the Databricks CLI
  against the live host stays outside pytest.

## Azure, Databricks, and cost

Names (live, reused — nothing new is created by this spec):

| Item | Name |
|---|---|
| Resource group | `rg-iris-ml-dev` |
| Workspace | `dbw-iris-ml-dev` (`https://adb-7405619226406985.5.azuredatabricks.net`) |
| Catalog.schema.model | `dbw_iris_ml_dev.develop.iris_species` |
| Endpoint | `iris-species-dev` (serverless CPU, Small, scale-to-zero on) |
| Secret scope | `kv-iris-ml-dev-7405` |
| Variable group (CI) | `iris-develop` |
| Region | East US |

Endpoint settings stay: CPU, Small, `scale_to_zero_enabled: true`,
`auto_capture_config.enabled: false` (legacy form was rejected in PR #7;
re-enabling capture is out of scope). Cost facts live in
`docs/cost-sheet.md` / `docs/cost-tracker.md` and are not repeated here;
no dollar rate is invented in this spec.

## Branch and review rules

- `develop` is the default branch. Implementation lives on
  `feature/databricks-jobs-serving`, PRs into `develop` only. Never push
  `ppe` / `prod`.
- CI runs on the PR (pytest, ruff, `bundle validate`). CD (`bundle
  deploy`, `bundle run`) lives in a separate gated stage/branch pattern
  taken from `origin/develop`'s `azure-pipelines-cd.yml` and never runs on
  a PR.
- Do not merge until the human approves. Do not commit `.env`, `.venv`,
  `mlruns/`, `mlruns.db`, `.databricks/`, or `.agents/`.

## Boundaries

- Always: reuse `IrisPyfunc` / `score_forest` / `validate_rows` verbatim;
  keep the four feature names and exact error sentences; install serving
  deps only from `requirements-serving.txt`; tag every job and run.
- Ask first: any new Azure/Databricks resource, any new secret, any change
  to serving pins, any `ppe`/`prod` content.
- Never: commit secrets or compute IDs, run `bundle deploy` / `bundle
  run` / `--register` during implementation, invent a DBU dollar rate, or
  retrain inside tests.

## Success criteria

- [ ] `resources/jobs.yml` defines exactly two jobs with the names,
  tasks, computes, params, and tags in the Jobs section.
- [ ] The notebook opens and runs cell-by-cell on a personal compute with
  only widget/env inputs (no code edits); the script runs with
  `uv run python notebooks/train_register.py` (log-only) with no Databricks
  dependency.
- [ ] Every configurable value in both jobs comes from a widget, env var,
  or bundle variable; secrets come only from the secret scope with env
  fallback; `dbutils` is never imported at module top level in a way that
  breaks local runs.
- [ ] `databricks bundle validate -t develop` passes against the live host.
- [ ] `uv run pytest -q` and `uv run ruff check .` pass, including the new
  contract test.
- [ ] Postman collection + environment exist, parse as JSON, and contain
  setosa then virginica requests asserting `prediction.species` and both
  `layman` strings. Live execution against `iris-species-dev` waits for
  the approved v6 deploy and is not part of implementation.
- [ ] No secret, token, compute ID, or dollar rate is committed
  (`git status --short`, `git diff --check` clean of them).

## Open questions

None. `personal_compute_id` is intentionally a deploy-time `--var`, not a
committed value — that is a design choice, not an undecided item. Cloud
deploy/run stays blocked until `docs/cost-sheet.md` is approved in a
PR comment. That is a gate, not an undecided design choice.

## Out of scope

- Running `bundle deploy`, `bundle run`, or `--register` (all gated).
- Bumping `entity_version` to 6 (happens only after v6 exists).
- Re-enabling inference-table capture, Lakehouse monitoring, or drift
  alerts.
- `ppe` / `prod` targets, promotion pipeline, UAE North.
- OIDC / workload-identity migration; RBAC changes.
- Full `features/` / `training/` / `serving/` folder restructure.
- New LLM API calls, keys, or spending.
