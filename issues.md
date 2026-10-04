# Issues

Log of defects in this repo. Newest first. `CHANGELOG.md` records what shipped. This file records what broke, and the fix.

## How this file stays current

Update this file in the same change that finds or fixes a defect. Do not wait for a later docs pass.

1. Add a row at the top of the matching table. Use the next `ISS-` number.
2. While it is open, put it under **Open**. When the fix is in the tree, move the row to **Fixed** and fill **Fix** and **Commit**.
3. One defect per row. A second attempt at the same defect updates the existing row.
4. Write the symptom and the cause. Do not paste secrets, tokens, or host credentials.

Cursor agents follow `.cursor/rules/issues-log.mdc`, which requires this update.

## Open

| ID | Found | Area | Issue | Notes |
|---|---|---|---|---|
| ISS-021 | 2026-10-04 | CI | Azure CI (`iris-ml-prod-test-ci`) fails about 45 seconds after the agent starts. GitHub CI on the same commits passes. Build 52 failed on the same clock with the variable group removed, so the run dies before sync. | Log page requires an Azure DevOps sign-in. uv is installed from the official script and path filters use `**`. Those YAML changes did not move the 45-second failure. |
| ISS-020 | 2026-10-04 | Bundle | Deploy path `/Workspace/Shared/.bundle/iris-ml-prod-test/<target>` is writable by every workspace user. | CLI warning on `bundle deploy` for develop, ppe, and prod. Move `root_path` off `/Shared` or grant `CAN_MANAGE` only to the owning principal. |

## Fixed

| ID | Found | Area | Issue | Fix | Commit |
|---|---|---|---|---|---|
| ISS-019 | 2026-10-04 | Bundle | `bundle validate` failed: targets set `git_branch` but `databricks.yml` never declared the variable. | Declare `git_branch` (default `develop`; prod target sets `main`). | `8060f31` |
| ISS-018 | 2026-10-04 | Jobs | Nine standalone jobs never ran: `develop`/`ppe`/`prod` copies of `iris-train-notebook-personal`, `iris-train-script-serverless`, and `iris-infer-script-serverless`. | Remove `databricks/tasks/` from the bundle. Redeploy develop, ppe, and prod. Keep the three `*-iris-ml-job-pipeline` jobs, which have runs. | `8060f31`. Workspace jobs deleted 2026-10-04 |
| ISS-017 | 2026-10-04 | CD | Azure CI did not put the pinned Databricks CLI on `PATH` in the same step that called it. | Install CLI 0.272.1 on `PATH` in that step. | `3c1cce1` |
| ISS-016 | 2026-10-04 | Serving | The endpoint served a hardcoded model version, so a new alias from the train job was ignored. PPE and prod also needed their own schemas. | Serve the env alias (`@develop` / `@ppe` / `@prod`) that the job just registered. | `3c1cce1` |
| ISS-015 | 2026-10-04 | CD | CD checked `develop-iris-species`, `ppe-iris-species`, and `prod-iris-species` before those endpoints existed. | Create a missing endpoint with `serving-endpoints create --no-wait`, then check it. | `f3a238a` |
| ISS-014 | 2026-10-04 | CI | Develop CI failed ruff E501 on a notebook print longer than 100 characters. | Wrap the print. | `f3a238a` |
| ISS-013 | 2026-10-04 | CD | Databricks CLI 0.272 rejects a positional endpoint name when `--json` is set. CD failed after the train-infer job had already succeeded. | Put the endpoint name inside the create JSON. | `fc75fed` |
| ISS-012 | 2026-10-04 | Jobs | Serverless has no Databricks CLI username, so a relative MLflow experiment name failed validation. | Fall back to `/Shared/<experiment>`. | `b81e11f` |
| ISS-011 | 2026-10-04 | Jobs | `spark_python_task` execs the script, so `__file__` is missing and the repo root cannot be resolved. | Walk the working directory or the bundle files path. | `f46bb4a` |
| ISS-010 | 2026-10-04 | Jobs | Train and infer imported `python-dotenv`, which is not in the serverless serving pins, so the tasks never started. `iris_model` was also not on `sys.path`. | Load `.env` only when dotenv is installed. Insert `src/` on `sys.path`. | `42b3250` |
| ISS-009 | 2026-10-04 | Jobs | Serverless treated the uploaded `requirements-serving.txt` path as a pip package name. `iris-ml-job-pipeline` failed during library install. | Depend on `-r ../../requirements-serving.txt`. | `7c85847` |
| ISS-008 | 2026-10-04 | CD | `bundle deploy` of the serving endpoint waited on container startup, so the train-infer job never started. | Keep the endpoint YAML out of the bundle include. Deploy jobs, run `iris-ml-job-pipeline`, then create the endpoint with `--no-wait`. | `e54d2c3` |
| ISS-007 | 2026-10-04 | CD | Gated CD deployed the bundle and never ran `iris-ml-job-pipeline`. An unpinned CLI also hit an expired Terraform provider key. | Run the pipeline after deploy. Pin Databricks CLI 0.272.1. | `c59ff9d` |
| ISS-006 | 2026-10-04 | CD | A leftover deploy lock owned by the workspace user blocked GitHub CD before the train-infer job could start. | Force the lock on the single-user Shared bundle deploy. | `9916db9` |
| ISS-005 | 2026-10-04 | CD | GitHub CD used `databricks/setup-cli@v0.2`, which no longer resolves, so the workflow died before checkout finished. | Pin the action to `v1.19.0`. | `acf37e5` |
| ISS-004 | 2026-10-04 | Serving | Databricks rejects `auto_capture_config` on endpoint create, including `enabled: false`. That blocked deploy before the pipeline could run. | Remove `auto_capture_config` from the endpoint YAML. An earlier change only set it to disabled (`7b8599d`). | `a49a065` |
| ISS-003 | 2026-09-30 | Training | The teaching notebook did not log the model with the same serving pins, signature, and alias calls as `train_register.py`. | Match pip requirements, signature, code paths, and `set_registered_model_alias`. | `4cf18e8` |
| ISS-002 | 2026-09-27 | CI | `pywin32` in the compiled requirements has no Linux wheel, so GitHub and Azure CI could not install. | Mark the pin Windows-only. | `0e1eebe` |
