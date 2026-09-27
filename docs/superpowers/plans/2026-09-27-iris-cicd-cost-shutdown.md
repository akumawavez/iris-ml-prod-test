# Iris CI/CD + $10 cost control + zero-spend shutdown — Implementation Plan

> **For agentic workers:** implement inline in this session (execution method
> already supplied: worktree `feature/cicd-cost-shutdown`, then PR into
> `develop` and merge). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire GitHub Actions CI + Azure DevOps PR CI (test-only), add gated
manual-only CD, cap spend at $10/mo with budget alerts, document 30-minute
cost tracking, provide a disable/delete-and-restore guide, and add a POST
inference test — all without creating or calling any cloud resource.

**Architecture:** CI stays test-only (`pytest`, never `databricks bundle
deploy`). CD lives in separate files that are manual-trigger-only and are not
created as real pipelines until cost approval. Cost control is a $10 Azure
budget (Bicep + guarded script, never applied here) plus a read-only snapshot
script run every 30 min of active use. Shutdown is docs-first: disable/stop in
place, delete only behind a second explicit flag, backup before anything.

**Tech Stack:** GitHub Actions YAML, Azure DevOps YAML, Azure Consumption
budgets (Bicep), PowerShell (guarded scripts), Python `urllib` (serving POST),
pytest contract tests.

**Spec:** `docs/superpowers/specs/2026-09-27-iris-develop-serving-design.md`
(response contract, branch rules, no-invented-rates rule all still apply).

## Global Constraints

- `develop` is the default branch; PRs target `develop` only; never touch `ppe`/`prod`.
- `azure-pipelines.yml` (CI) must never contain `databricks bundle deploy`.
- Never invent USD/DBU rates — dollar rate stays TBD unless copied from an official page.
- Never run `az ... create`, `databricks bundle deploy`, or any `-Confirm` setup script.
- Never write tokens/keys into code, docs, or chat; serving auth is env-vars-only.
- No secrets committed (`git status --short`, `git diff --check` clean).
- CHANGELOG entry for user-facing changes.

---

### Task 1: GitHub CI (test-only, runs only when required)

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `tests/test_pipeline_contract.py` (add `test_github_ci_runs_pytest_only_when_required`)

**Interfaces:**
- Consumes: `requirements.txt`, `pytest` suite (9 tests, ~80 s).
- Produces: CI that runs on `pull_request` → `develop` and `push` → `develop`
  only, with `paths` filters (code/model/pipeline changes), `concurrency`
  cancel-in-progress, no schedules, no deploy step.

- [ ] **Step 1: Write `.github/workflows/ci.yml`** (checkout, setup-python 3.13,
  pip install requirements, `python -m pytest -q`).
- [ ] **Step 2: Extend contract test** — assert `pytest` present, `deploy`
  absent, triggers limited to develop, `paths`/`concurrency` present.
- [ ] **Step 3: Run** `uv run pytest -q` — Expected: PASS.
- [ ] **Step 4: Commit** — `git add .github/workflows/ci.yml tests/test_pipeline_contract.py`
  + `git commit -m "ci: add GitHub test-only CI that runs only when required"`.

### Task 2: Tighten Azure DevOps CI + wire GitHub PRs

**Files:**
- Modify: `azure-pipelines.yml`
- Modify: `docs/guides/azure-devops.md` (short wiring note — GitHub service connection already documented; add path-filter + batch note)
- Modify: `tests/test_pipeline_contract.py` (add `test_azure_ci_runs_only_when_required`)

**Interfaces:**
- Consumes: Task 1 triggers philosophy.
- Produces: `azure-pipelines.yml` with `batch: true`, `paths.include`
  (src/tests/models/requirements/pyproject/pipelines) + `exclude` (*.md-only
  effect), PR trigger on `develop` only, still no deploy step.

- [ ] **Step 1: Edit pipeline triggers** keeping `pytest`, `develop`, no-deploy intact.
- [ ] **Step 2: Extend contract test** — assert `batch: true`, PR→develop only, no schedules.
- [ ] **Step 3: Run** `uv run pytest tests/test_pipeline_contract.py -q` — Expected: PASS.
- [ ] **Step 4: Commit** — `git commit -m "ci: run Azure pipeline only when required (batch + path filters)"`.

### Task 3: Manual-only CD pipelines (exist, never auto-run, never created yet)

**Files:**
- Create: `azure-pipelines-cd.yml`
- Create: `.github/workflows/cd.yml`
- Modify: `tests/test_pipeline_contract.py` (add `test_cd_is_manual_only_and_gated`)

**Interfaces:**
- Consumes: `databricks.yml` (develop target), variable group `iris-develop` (future).
- Produces: AzDO CD with `trigger: none` + `pr: none` + `Environment: iris-develop`
  approval + variable group; GitHub CD with `workflow_dispatch` only +
  `environment: develop`. Both files state at the top: DO NOT create/enable
  until cost approval. CI files never reference them.

- [ ] **Step 1: Write both CD files** (stages: bundle validate → approval → deploy `-t develop` only).
- [ ] **Step 2: Extend contract test** — assert no CI triggers (`trigger: none`,
  `pr: none` / `workflow_dispatch` only), environment gating present, CI files
  contain no `bundle deploy`.
- [ ] **Step 3: Run** contract tests — Expected: PASS.
- [ ] **Step 4: Commit** — `git commit -m "cd: add manual-only gated deploy pipelines (disabled until approval)"`.

### Task 4: $10 budget, alerts, and 30-minute cost tracking

**Files:**
- Create: `docs/cost-tracker.md` (cap $10, alert tiers 50/80/100%, 30-min snapshot cadence, md-vs-html ownership)
- Create: `docs/cost-dashboard.html` (calculator wired to $10 cap)
- Create: `infra/budget.bicep` (Consumption budget $10 + action group params, no hardcoded email)
- Create: `scripts/setup_budget.ps1` (GUARDED `-Confirm`; creates budget + action group; never run here)
- Create: `scripts/cost_snapshot.ps1` (SAFE read-only: `az consumption` query + DBU reminder; `-UpdateTracker` rewrites one snapshot block)
- Modify: `tests/test_pipeline_contract.py` (add `test_cost_control_caps_at_ten_dollars`)

**Interfaces:**
- Consumes: nothing secret; rate stays TBD (no invented numbers).
- Produces: `docs/cost-tracker.md` = signed record, `docs/cost-dashboard.html` =
  calculator; alerts at $5/$8/$10; snapshot cadence: every 30 min of active endpoint use.

- [ ] **Step 1: Write tracker + dashboard + bicep + scripts.**
- [ ] **Step 2: Extend contract test** — assert `$10`/`10.00` cap, `50`/`80`/`100` tiers,
  `30 min` cadence, `setup_budget.ps1` contains `-Confirm` guard.
- [ ] **Step 3: Run** contract tests — Expected: PASS.
- [ ] **Step 4: Commit** — `git commit -m "cost: cap spend at $10 with alerts and 30-minute tracking"`.

### Task 5: Zero-spend shutdown + backup/restore guide

**Files:**
- Create: `docs/teardown-and-restore.md` (disable-first order: endpoint stop →
  pipelines disabled → optional RG delete behind second flag; backup-first: endpoint
  JSON, bundle YAMLs already in git, UC model lineage; restore steps reversed)
- Create: `scripts/teardown_dev.ps1` (GUARDED `-Confirm`; default disables/stops only;
  `-IncludeDelete` required for RG delete; always exports backup JSONs first; never run here)
- Modify: `tests/test_pipeline_contract.py` (add `test_shutdown_guide_and_script_exist_and_are_guarded`)

**Interfaces:**
- Consumes: resource names from `docs/cost-sheet.md`.
- Produces: guide + script; no cloud command executed.

- [ ] **Step 1: Write guide + script.**
- [ ] **Step 2: Extend contract test** — assert guide names disable-before-delete order,
  script has `-Confirm` + `-IncludeDelete` guards and no uncommented `az group delete`.
- [ ] **Step 3: Run** contract tests — Expected: PASS.
- [ ] **Step 4: Commit** — `git commit -m "ops: add zero-spend shutdown and restore guide with guarded script"`.

### Task 6: Serving POST inference test + doc

**Files:**
- Create: `scripts/test_serving.py` (default `--dry-run`: validates payload locally via
  `score_model`, no network; `--live` POSTs with `urllib` using `DATABRICKS_HOST`/`DATABRICKS_TOKEN` env only)
- Create: `docs/serving-inference-test.md` (endpoint URL shape, curl + python samples,
  setosa/virginica expectations, cost note: calls keep endpoint warm, idle 30 min → scale-to-zero)
- Modify: `tests/test_pipeline_contract.py` (add `test_serving_test_script_is_safe_by_default`)

**Interfaces:**
- Consumes: `score_model` response contract; endpoint name `iris-species-dev`.
- Produces: doc + script; no live call executed (no secrets, no spend).

- [ ] **Step 1: Write script (stdlib only) + doc with recorded LOCAL sample labeled as such.**
- [ ] **Step 2: Extend contract test** — assert script defaults to dry-run, reads token
  from env only, doc contains POST path `/serving-endpoints/…/invocations`.
- [ ] **Step 3: Run** `uv run pytest -q` full suite + `python scripts/test_serving.py --dry-run` — Expected: PASS.
- [ ] **Step 4: Commit** — `git commit -m "test: add serving POST inference check with dry-run default"`.

### Task 7: Index, changelog, push, PR, merge

**Files:**
- Modify: `README.md` (link new docs: cost tracker, teardown, inference test, CD gating note)
- Create: `CHANGELOG.md` (Unreleased entry)
- Modify: `docs/cost-sheet.md` (append pointer to `docs/cost-tracker.md` $10 cap — no rate invention)

**Interfaces:**
- Consumes: Tasks 1–6 files.
- Produces: PR `feature/cicd-cost-shutdown` → `develop`, merged only after this session's
  verification (user explicitly requested merge).

- [ ] **Step 1: Update README + CHANGELOG + cost-sheet pointer.**
- [ ] **Step 2: Run FULL suite** `uv run pytest -q` + `git diff --check` — Expected: green/clean.
- [ ] **Step 3: Push + open PR** (`gh pr create --base develop`), **merge** (`gh pr merge --merge`),
  verify `git worktree list` state. Ruling: user explicitly asked to merge; merge-via-PR
  honors "PRs into develop only".
- [ ] **Step 4: Report** — rulings, deferred items, untracked-file reconciliation warning
  (main checkout has untracked namesakes that will need handling on pull).
