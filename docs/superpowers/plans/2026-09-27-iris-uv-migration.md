# uv migration — Implementation Plan

> **For agentic workers:** implement inline in worktree
> `feature/uv-migration`, then PR into `develop` and merge on approval.

**Goal:** Make uv the only toolchain: install via `uv sync`, run via
`uv run`, lint via `uv run ruff`, freeze via `uv pip compile --universal`.

**Spec:** `docs/superpowers/specs/2026-09-27-iris-develop-serving-design.md`
(unchanged behavior; toolchain change only).

## Global Constraints

- `develop`-only PRs; CI stays test-only, never `databricks bundle deploy`.
- No invented rates; no cloud commands; no secrets in git.
- `requirements.txt` stays as the compiled output (Databricks/AML readers).

## Tasks

### Task 1: Real uv project (done when `uv sync --extra dev` works from scratch)

- `pyproject.toml`: `[project] iris-model 0.1.0`, `requires-python >=3.12`
  (pinned `shap==0.52` needs >=3.12 — ruling, see below), prod deps
  joblib/mlflow/pandas/scikit-learn/shap, dev extras pytest/pyyaml/ruff/pre-commit,
  setuptools src layout, pytest + ruff config (per-file-ignore B905 for legacy
  `train.py` zip; format-exclude legacy `score.py` whose collapse would breach E501).
- `.python-version` = 3.13. `uv lock` committed.
- Verify: `uv run pytest -q` 15 green, `uv run ruff check .` green,
  `uv run ruff format --check .` green.

### Task 2: Frozen requirements via compile (done when Linux CI installs cleanly)

- `uv pip compile --universal pyproject.toml -o requirements.txt` (universal
  keeps `; sys_platform == "win32"` markers — plain compile dropped them and
  broke Linux CI; header records the command for reproducibility).
- Verify: setosa CLI via editable install with no PYTHONPATH.

### Task 3: uv-only CI (done when both CIs use `uv sync --locked`)

- `.github/workflows/ci.yml`: `astral-sh/setup-uv` + `uv sync --locked --extra dev`,
  `uv run pytest -q`, ruff check + format; `uv.lock` in paths.
- `azure-pipelines.yml`: `pip install uv`, same sync/test/lint; `uv.lock` in paths.
- Contract tests: assert uv sync/run + ruff in both CIs, no
  `pip install -r requirements`, plus `test_uv_project_layout`.

### Task 4: Docs + merge

- README score-locally → uv; CHANGELOG entry; full suite green;
  `git diff --check` clean; push, PR into `develop`, merge on approval.

## Rulings

- Python floor 3.11 → 3.12: uv's universal resolver proved `shap==0.52`
  unsatisfiable on 3.11. Cost if wrong: none (CI/dev already on 3.13).
- Legacy `score.py` formatting frozen via ruff format-exclude instead of
  reformatting (collapse would breach E501). Cost if wrong: style-only.
