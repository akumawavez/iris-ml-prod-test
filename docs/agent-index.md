# Agent index

Files that tell an agent how to work in this repo: instructions, Cursor
hooks, the Iris plugin, and the local skill packs. The Markdown map is
[guides/README.md](guides/README.md). The rest of the tree is
[codebase-index.md](codebase-index.md).

## Instructions the agent reads first

| File | Role |
|---|---|
| [AGENTS.md](../AGENTS.md) | Promotion path, the check commands, and the hard stops: no secrets in git, no `bundle deploy` in CI, no CD until the cost tracker is approved |
| [.cursor/rules/issues-log.mdc](../.cursor/rules/issues-log.mdc) | Always on. Record defects in `issues.md` in the same change that finds or fixes them |
| [.cursor/rules/azure-devops-only.mdc](../.cursor/rules/azure-devops-only.mdc) | Always on. CI and CD run only in Azure DevOps. GitHub Actions stays disabled |
| [plugins/iris-agent/rules/branch-and-secrets.mdc](../plugins/iris-agent/rules/branch-and-secrets.mdc) | Always on. Protected branches, pull request target, secret files, CI stays test-only |
| [plugins/iris-agent/rules/azure-devops-only.mdc](../plugins/iris-agent/rules/azure-devops-only.mdc) | Always on. Same Azure DevOps-only rule, packaged with the plugin |
| [plugins/iris-agent/rules/python-style.mdc](../plugins/iris-agent/rules/python-style.mdc) | Applies to `*.py`. Ruff line length 100, and `uv` is the only installer |

## Cursor project hooks

[.cursor/hooks.json](../.cursor/hooks.json) is what a trusted workspace and
cloud agents load. Each hook runs a script under `plugins/iris-agent/scripts/`.

| Hook | Script | What it does |
|---|---|---|
| `beforeShellExecution` | [guard_shell.py](../plugins/iris-agent/scripts/guard_shell.py) | Blocks force-push of `develop`, `ppe`, and `main`, blocks `git commit --no-verify`, and blocks commands that print `.env`, `.pem`, or `.key` |
| `beforeReadFile` | [guard_read.py](../plugins/iris-agent/scripts/guard_read.py) | Keeps those secret files out of context. `.env.example` stays readable |
| `afterFileEdit` | [format_python.py](../plugins/iris-agent/scripts/format_python.py) | Runs `ruff format` and `ruff check --fix` on workspace Python. A missing `uv` does not block the edit |
| shared helper | [hook_io.py](../plugins/iris-agent/scripts/hook_io.py) | Reads the hook payload and writes the allow or deny response |

Tests for those guards: [tests/test_agent_hooks.py](../tests/test_agent_hooks.py).

Pre-commit is separate from the hooks. The config is
[.pre-commit-config.yaml](../.pre-commit-config.yaml). Install it with
`uv run pre-commit install`.

## Iris MLOps plugin

Marketplace entry: [.cursor-plugin/marketplace.json](../.cursor-plugin/marketplace.json)
points at `plugins/iris-agent`. Plugin manifest:
[plugin.json](../plugins/iris-agent/.cursor-plugin/plugin.json).

The plugin's own [hooks.json](../plugins/iris-agent/hooks/hooks.json) calls
`./scripts/` so an installed copy can find the same three guards.

| File | Role |
|---|---|
| [README.md](../plugins/iris-agent/README.md) | What the plugin packages and how to enable it |
| [agents/mlops-reviewer.md](../plugins/iris-agent/agents/mlops-reviewer.md) | Review agent. Branch rules, secrets, test-only CI, gated CD. It does not deploy |
| [commands/check.md](../plugins/iris-agent/commands/check.md) | Command that runs pytest, ruff, and pre-commit |
| [skills/local-score/SKILL.md](../plugins/iris-agent/skills/local-score/SKILL.md) | Score one row from `models/iris_species` and run the local gate |

## Course skill (in git)

[codebase-to-course](../.cursor/skills/codebase-to-course/SKILL.md) is a
Cursor project skill. It turns a repo into a self-contained HTML course.
The course already built from this repo is
[agentic-productionalisation/index.html](courses/agentic-productionalisation/index.html):
six sittings, three days a week for two weeks, on Databricks MLOps:
the loop, Asset Bundles, jobs, MLflow registry, serving endpoints, and
the practices this repo follows. The longer reading list is
[productionalisation-study-plan.md](guides/productionalisation-study-plan.md).

## Local skill packs

`.agents/` is gitignored. These packs are installed on this machine for the
agent. They are not part of the commit. Each pack starts at `SKILL.md`.
Reference notes sit in the same folder.

| Pack | Entry | What it covers |
|---|---|---|
| azure-databricks | `.agents/skills/azure-databricks/SKILL.md` | Azure Databricks architecture, config, deploy, security, limits |
| azure-devops | `.agents/skills/azure-devops/SKILL.md` | Azure DevOps REST API v7.1, OAuth or PAT |
| databricks-core | `.agents/skills/databricks-core/SKILL.md` | CLI install, auth, and data exploration |
| databricks-dabs | `.agents/skills/databricks-dabs/SKILL.md` | Declarative Automation Bundles: validate, deploy, run |
| databricks-docs | `.agents/skills/databricks-docs/SKILL.md` | Databricks documentation index |
| databricks-jobs | `.agents/skills/databricks-jobs/SKILL.md` | Lakeflow Jobs tasks, triggers, notifications |
| databricks-ml-training | `.agents/skills/databricks-ml-training/SKILL.md` | Training, pyfunc, feature store, feature views |
| databricks-model-serving | `.agents/skills/databricks-model-serving/SKILL.md` | Serving endpoints |
| databricks-python-sdk | `.agents/skills/databricks-python-sdk/SKILL.md` | Python SDK, Connect, CLI, and REST |
| databricks-serverless-migration | `.agents/skills/databricks-serverless-migration/SKILL.md` | Classic compute to serverless |
| databricks-unity-catalog | `.agents/skills/databricks-unity-catalog/SKILL.md` | Privileges, storage, and securables |
| mlflow-onboarding | `.agents/skills/mlflow-onboarding/SKILL.md` | MLflow onboarding |
| searching-mlflow-docs | `.agents/skills/searching-mlflow-docs/SKILL.md` | Search the MLflow docs index |

Related guides, committed with the repo:
[cursor-best-practices.md](guides/cursor-best-practices.md) and
[cursor-pro-agent-models.md](guides/cursor-pro-agent-models.md).
