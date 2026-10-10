# Databricks bundle best practices

How this repo writes and deploys a Databricks Asset Bundle. Newer Databricks
docs call the same feature **Declarative Automation Bundles**. The CLI
command is still `databricks bundle`.

Official references:
[Asset Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/),
[developer best practices](https://docs.databricks.com/aws/en/developers/best-practices).

The file map for this project is [databricks-asset-bundles.md](databricks-asset-bundles.md).
Which git branch may deploy which target is
[eli25-code-movement.md](eli25-code-movement.md).

## 1. One bundle for the whole project

One git repo. One `databricks.yml`. Every environment of this model
(`develop`, `ppe`, `prod`) is a target in that same bundle. A second
product gets a second bundle. A second repo per environment drifts.

`databricks.yml` stays thin: bundle name, the wheel artifact, and
`include`. Variable defaults and resource bodies live under `databricks/`.

| Path | What it owns |
|---|---|
| `databricks.yml` | Name, wheel build, and `include` |
| `databricks/variables.yml` | Shared variable defaults |
| `databricks/jobs/` | One job per file: train and infer |
| `databricks/targets/` | One target per file: host, mode, and variable overrides |
| `databricks/artifacts/` | Endpoint shape, included with the jobs and targets |

## 2. Override names in the target, once

Anything that changes by environment is the bundle variable `env_suffix`
(`develop`, `ppe`, or `prod`). `git_branch` is the only other override,
because prod's git branch is `main`.

Job, endpoint, experiment, catalog schema, and alias all append that
variable: `iris-ml-train-${var.env_suffix}`, `iris-ml-infer-${var.env_suffix}`,
`iris-species-${var.env_suffix}`,
`dbw_iris_ml_dev.${var.env_suffix}.iris_species`. Copying a job file per
environment is how the three copies fall out of date.

This repo's pairs:

| Git branch | Target file | Databricks target |
|---|---|---|
| `develop` | `databricks/targets/develop.yml` | `develop` |
| `ppe` | `databricks/targets/ppe.yml` | `ppe` |
| `main` | `databricks/targets/prod.yml` | `prod` |

`main` is the prod git branch. The Databricks target stays named `prod`.

## 3. Paths are relative to the file that contains them

A path inside `databricks/jobs/iris_ml_train.yml` is relative to
that file, so the wheel is `../../dist/*.whl` and the task script is
`../../notebooks/train_register.py`. A path inside `databricks.yml` is
relative to the repo root, so the wheel artifact `path` is `.`.

## 4. Push the library as a wheel

`src/iris_model` is the uv package. The bundle artifact builds it:

```yaml
artifacts:
  iris_model:
    type: whl
    path: .
    build: uv build --wheel
    dynamic_version: true
```

The job environment depends on `../../dist/*.whl`. Deploy uploads the
wheel and the serverless environment installs it before the tasks start.
Tasks import `iris_model`. They do not `pip install` the package and they
do not put `src` on `sys.path`.

`dynamic_version: true` stamps the wheel on each deploy so serverless does
not keep running an older cached copy. Requires Databricks CLI 0.245.0 or
newer. This repo's CD installs 0.272.1.

`requirements-serving.txt` is the pin file stored on the logged model for
the endpoint. It is not the job's library install.

## 5. Production mode for shared environments

Each target sets `mode: production`. Resource names stay exactly the
names in the YAML, with the environment as a suffix
(`iris-ml-train-develop`, `iris-ml-infer-develop`, and the same pattern for ppe and prod).

`mode: development` is for a personal sandbox. It prefixes names with the
deploying user and can pause schedules. This teaching workspace is shared,
so develop, ppe, and prod all use production mode. `develop` is
`default: true`.

## 6. Isolate environments by name, then by workspace

While develop, ppe, and prod share one host, every job, endpoint,
experiment, alias, and Unity Catalog schema carries the environment name.
That is what stops a develop deploy from overwriting prod.

`root_path` includes the bundle name and the target:

```text
/Shared/.bundle/${bundle.name}/${bundle.target}
```

Databricks recommends a folder the team owns, with `CAN_MANAGE` only for
that team, once a second team can open the workspace. `/Workspace/Shared`
is writable by every user. Move `root_path` off `/Shared` before that
happens. Giving ppe or prod its own host is a host change in that target
file, then the same git promotion. See the
[promotion runbook](../runbooks/promote-ppe-prod-and-uae.md).

## 7. Validate in CI. Deploy from gated CD

| Command | Spends? | When |
|---|---|---|
| `databricks bundle validate -t develop` | No | After every bundle edit. CI runs this for `develop`, `ppe`, and `prod` |
| `databricks bundle deploy -t <target>` | Yes | Manual `azure-pipelines-cd.yml`, after [cost-tracker.md](../cost-tracker.md) is approved |
| `databricks bundle run iris-ml-train -t <target>` then `iris-ml-infer` | Yes | Same gated pipeline, only when `runMode` is `train-and-serve` |

Run validate for every target you might deploy. A YAML error in `prod.yml`
should fail on the develop pull request, before anyone promotes.

CD deploys a target only from its git branch. `scripts/assert_deploy_branch.py`
stops the run when the branch and the target disagree.

GitHub Actions `cd.yml` is disabled (`if: false`). Azure DevOps is the
pipeline that deploys.

## 8. Keep deploy from waiting on the wrong resource

`databricks.yml` includes `databricks/variables.yml`,
`databricks/artifacts/*.yml`, `databricks/jobs/*.yml`, and
`databricks/targets/*.yml`. Deploy can wait while the endpoint container
starts. `scripts/apply_served_version.py` still uses
`serving-endpoints create --no-wait` and then points the endpoint at the
alias version.

Add a resource to `include` when deploy can create it without waiting on
a long-running side effect. Apply the slow one in an explicit later step.

## 9. One job definition per pipeline

Train and infer are separate jobs: `iris-ml-train` and `iris-ml-infer`.
CD runs train, then infer, only when `runMode` is `train-and-serve`.
A failed train does not score, because infer is the next step and does
not start on its own. The default `serve` starts neither job.

Do not add a second copy of the same job for "just in case." Standalone
train and infer jobs were removed because they never ran.

No all-purpose cluster and no SQL warehouse in the bundle. The job is
serverless. The endpoint is CPU, Small, scale-to-zero.

## 10. Tag what you create

Jobs and the endpoint carry `project`, `env`, `owner`, and `managed-by: dab`.
`owner` is a tag. It is not an access-control list. Tags are how a bill
gets tied back to the YAML.

## 11. Secrets stay out of the bundle

Variable names and variable-group names are safe in git. Token values,
client secrets, and connection strings are not. Local values live in
`.env`. CD uses the service principal in `iris-develop`, `iris-ppe`, or
`iris-prod`, and it unsets `DATABRICKS_TOKEN` before the CLI runs.

`.databricks/`, `dist/`, and `.env` stay gitignored. The wheel is built
at deploy time.

## 12. The YAML wins over the workspace UI

A click in the job or endpoint UI lasts until the next deploy, which
writes the YAML back over it. Change the job, the wheel, the schedule, or
the endpoint size in git, then deploy that target from its branch.

Rollback is the previous commit, deployed to the same target, from that
target's git branch.

## Checklist before a bundle change is merged

1. Names that differ by environment are `${var.*}`, overridden in `databricks/targets/`.
2. `databricks bundle validate -t develop`, `-t ppe`, and `-t prod` succeed.
3. No secret value in the YAML.
4. The job still installs the uv wheel, and tasks still import `iris_model`.
5. Deploy of this target is still gated on its git branch.
6. The change does not add `bundle deploy` to `azure-pipelines.yml`.
