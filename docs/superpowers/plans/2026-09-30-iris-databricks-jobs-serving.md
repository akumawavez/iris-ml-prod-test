# Iris Databricks jobs + serving Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two Databricks Jobs (notebook on personal compute, script on serverless) over the existing iris training logic, with env/dbutils/tags/uv wiring, a Postman collection, and DAB validate + gated CI — without deploying or registering anything.

**Architecture:** Thin wrappers only: `train_register.py` and the notebook gain a widget/env/secret/tag header and an `LLM_EXPLANATION_STYLE` switch; `IrisPyfunc`/`score_forest` stay verbatim. `resources/jobs.yml` declares both jobs; `databricks.yml` gains deploy-time variables. CI runs pytest + ruff + `bundle validate`; deploy/run/`--register`/v6 bump all wait for written cost approval.

**Tech Stack:** Python 3.11+, scikit-learn, MLflow 3.3.2, Databricks Asset Bundles, Azure DevOps Pipelines, Postman v2.1 collections, uv (compile locally, install compiled file on Databricks).

**Spec:** `docs/superpowers/specs/2026-09-30-iris-databricks-jobs-serving-design.md`

## Global Constraints

- UC model `dbw_iris_ml_dev.develop.iris_species`; endpoint `iris-species-dev`; workspace `https://adb-7405619226406985.5.azuredatabricks.net`; region East US.
- Serving pins come only from `requirements-serving.txt` (`cloudpickle==3.0.0 joblib==1.4.2 mlflow==3.3.2 numpy==1.26.4 pandas==2.2.3 scikit-learn==1.5.2 scipy==1.13.1 shap==0.46.0`); never `requirements.txt`.
- `FEATURES = ("sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm")`; `RandomForestClassifier(n_estimators=100, random_state=42)`.
- `LLM_EXPLANATION_STYLE` in (`concise`, `eli5`, `verbose`), default `concise`; local template only, never changes probabilities/SHAP/importances.
- Six per-job tag keys exactly: `project`, `env`, `task`, `compute`, `managed-by`, `owner`; bundle top-level tags add `cost-center: learning`.
- Secret scope `kv-iris-ml-dev-7405`; scope/key names committed, values never; compute IDs never committed (`${var.personal_compute_id}`, default `""`).
- Branch `feature/databricks-jobs-serving` from `develop`, PRs into `develop` only; never touch `ppe`/`prod`.
- NEVER run during implementation: `databricks bundle deploy`, `databricks bundle run`, `uv run python notebooks/train_register.py --register`, `az ... create`, `scripts/* -Confirm`.
- DoD: `uv run pytest -q` green, `uv run ruff check .` green, `databricks bundle validate -t develop` passes, no secrets in diff, CHANGELOG entry.

## Review Focus

- `dbutils` undefined outside Databricks (plain `uv run`, Jupyter) yet wrapper still resolves params — expect env/default fallback, never `NameError`. Pinned by Task 2 param-fallback test.
- `personal_compute_id` empty at validate time (default `""`) — expect `bundle validate` still passes; only deploy requires `--var`. Pinned by Task 4 validation test using the default.
- Secret scope unreachable locally (no Databricks auth) — expect env fallback and log-only run, never a crash. Pinned by Task 2 secret-fallback test.
- `LLM_EXPLANATION_STYLE` set to an unknown string — expect `concise` behavior, never a `KeyError`. Pinned by Task 2 style-fallback test.
- `requirements-serving.txt` drifts (e.g. `pywin32`/`pytest` sneaks back via recompile) — expect contract test failure naming the offending line. Pinned by Task 4 serving-pins test.

---

### Task 1: Branch and spec commit (Postman deferred per user 2026-09-30)

**Files:**
- Add (already written, untracked): `docs/superpowers/specs/2026-09-30-iris-databricks-jobs-serving-design.md`, `docs/superpowers/plans/2026-09-30-iris-databricks-jobs-serving.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: spec path above.
- Produces: branch with committed spec+plan; nothing else consumes it.
- Note: the Postman collection/environment moves to a post-plan follow-up. `tests/test_jobs_contract.py` is therefore first created in Task 2, not here.

- [ ] **Step 1: Confirm branch state (already set up — verify only)**

Run: `git branch --show-current` and `git status --short`
Expected: on `feature/databricks-jobs-serving`; status shows only the untracked spec/plan files.

- [ ] **Step 2: Append CHANGELOG entry**

Check `CHANGELOG.md` format first and follow it; one entry for this feature (no Postman mention).

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-09-30-iris-databricks-jobs-serving-design.md docs/superpowers/plans/2026-09-30-iris-databricks-jobs-serving.md CHANGELOG.md
git commit -m "docs: spec and plan for databricks jobs serving"
```

Expected: `git log --oneline -1` shows the commit; `git status --short` is clean.

### Task 2: Env/dbutils/tags/LLM wrappers on existing logic

**Files:**
- Modify: `notebooks/train_register.py`
- Modify: `notebooks/01_train_and_register.ipynb`
- Modify: `src/iris_model/narratives.py`
- Test: `tests/test_jobs_contract.py` (create — Postman test deferred, this file starts here)

**Interfaces:**
- Consumes: `IrisPyfunc`, `score_forest`, `FEATURES` (verbatim, no signature changes).
- Produces: `_get_param(name: str, default: str) -> str`, `_get_secret(scope: str, key: str, env_fallback: str = "") -> str`, `explain_layman(style: str, species: str, top_feature: str, share: float) -> str` consumed by Task 3 job params. Load the script in tests via `importlib.util.spec_from_file_location("notebooks_train_register", "notebooks/train_register.py")` (the `notebooks/` dir is not a package).

- [ ] **Step 1: Write the failing wrapper tests**

Create `tests/test_jobs_contract.py` with:

```python
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
    assert explain_layman("nonsense", "setosa", "petal_length_cm", 0.9) == explain_layman("concise", "setosa", "petal_length_cm", 0.9)

def test_secret_falls_back_without_dbutils(monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "notebooks_train_register", "notebooks/train_register.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.delenv("databricks-token", raising=False)
    assert m._get_secret("kv-iris-ml-dev-7405", "databricks-token") == ""
```

Run: `uv run pytest tests/test_jobs_contract.py -v`
Expected: FAIL (`_get_param` / `explain_layman` not defined).

- [ ] **Step 2: Implement the three helpers reusing existing logic**

In `train_register.py`: add `_get_param` / `_get_secret` per spec patterns (try `dbutils`, except → `os.getenv`); read the four env names; call `mlflow.set_tags` with the six keys; keep fit/log/register flow byte-identical otherwise. In `narratives.py`: add `explain_layman(style, ...)` dispatching among three pre-written templates. Mirror the header as the notebook's first cell (widgets with identical names/defaults).

- [ ] **Step 3: Run wrapper tests plus full suite**

Run: `uv run pytest -q` and `uv run ruff check .`
Expected: all PASS including the three new tests; existing score tests untouched.

- [ ] **Step 4: Commit**

```bash
git add notebooks/train_register.py notebooks/01_train_and_register.ipynb src/iris_model/narratives.py tests/test_jobs_contract.py
git commit -m "feat: env-driven dbutils wrappers with local fallback and llm style switch"
```

### Task 3: Jobs + bundle variables (no deploy)

**Files:**
- Create: `resources/jobs.yml`
- Modify: `databricks.yml`
- Test: `tests/test_jobs_contract.py` (append)

**Interfaces:**
- Consumes: `_get_param` names, `train_register.py` path, notebook path from Task 2.
- Produces: job names `iris-train-notebook-personal` / `iris-train-script-serverless` consumed by Task 5 CI docs.

- [ ] **Step 1: Write the failing jobs test**

Append:

```python
def test_two_jobs_personal_notebook_and_serverless_script():
    import yaml
    from pathlib import Path
    jobs = yaml.safe_load(Path("resources/jobs.yml").read_text())["resources"]["jobs"]
    assert set(jobs) == {"iris-train-notebook-personal", "iris-train-script-serverless"}
    assert jobs["iris-train-notebook-personal"]["tags"] == {"project": "iris-ml", "env": "develop", "task": "notebook", "compute": "personal", "managed-by": "dab", "owner": "${var.owner}"}
    assert "existing_cluster_id" in str(jobs["iris-train-notebook-personal"]) and "${var.personal_compute_id}" in str(jobs["iris-train-notebook-personal"])
    assert jobs["iris-train-script-serverless"]["tags"]["compute"] == "serverless"
    text = Path("resources/jobs.yml").read_text() + Path("databricks.yml").read_text()
    assert "databricks-token" not in text or "kv-iris-ml-dev-7405" in text
    assert "pywin32" not in Path("requirements-serving.txt").read_text().lower()
```

Run: `uv run pytest tests/test_jobs_contract.py::test_two_jobs_personal_notebook_and_serverless_script -v`
Expected: FAIL (`resources/jobs.yml` missing).

- [ ] **Step 2: Write `resources/jobs.yml` and extend `databricks.yml`**

Jobs per spec (notebook task + `existing_cluster_id: ${var.personal_compute_id}`; Python-file task + serverless `environments` on `requirements-serving.txt`; shared env/params/tags). `databricks.yml`: add `variables:` (`personal_compute_id` default `""`, `registered_model_name`, `experiment_name`, `owner: iris-learn`) + top-level `tags:` with `cost-center: learning`. Keep `ppe`/`prod` hosts `""`; keep endpoint at version `"5"`.

- [ ] **Step 3: Run jobs tests + validate (safe, read-only)**

Run: `uv run pytest tests/test_jobs_contract.py -v` then `databricks bundle validate -t develop`
Expected: tests PASS; validate passes with default vars (empty compute ID allowed at validate time).

- [ ] **Step 4: Commit**

```bash
git add resources/jobs.yml databricks.yml tests/test_jobs_contract.py
git commit -m "feat: two databricks jobs on personal and serverless compute"
```

### Task 4: CI validate wiring + docs close-out

**Files:**
- Modify: `azure-pipelines.yml` (add `bundle validate` step only; keep reconcile-with-develop note if file already has uv CI from `origin/develop`)
- Modify: `docs/secrets.md` (one paragraph: secret-scope pattern; no values)
- Test: none new (existing suite is the gate)

**Interfaces:**
- Consumes: job names from Task 3.
- Produces: PR-ready branch; nothing else consumes it.

- [ ] **Step 1: Add the validate step**

CI change is append-only: after pytest/ruff, `databricks bundle validate -t develop`. Assert locally that `azure-pipelines.yml` contains `bundle validate` and does NOT contain `bundle deploy` or `bundle run`.

- [ ] **Step 2: Run the full gates**

Run: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `databricks bundle validate -t develop`, `git diff --check`, `git status --short`
Expected: all green; status shows only intended files; no `.env`/tokens/IDs in diff.

- [ ] **Step 3: Push and open the PR (stop; do not merge, deploy, or run)**

Run: `git push -u origin feature/databricks-jobs-serving` then `gh pr create --base develop --head feature/databricks-jobs-serving --title "Databricks jobs (notebook + script) with serving path"`
Expected: PR open, CI runs test + validate only. Do NOT merge; do NOT run deploy/run/`--register`; do NOT bump endpoint to v6.

## Checkpoint: After Tasks 1-4

- [ ] PR into `develop` open with spec, plan, jobs, wrappers, contract tests, CHANGELOG (Postman deferred to follow-up)
- [ ] `bundle validate` green in CI; no deploy/run/register executed
- [ ] Human reviews plan output and approves merge; v6 registration + endpoint bump + Postman collection/live run are separate gated follow-ups
