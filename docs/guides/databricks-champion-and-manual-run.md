# Champion model and a manual run

Azure DevOps is the pipeline that runs. `azure-pipelines-cd.yml` is manual.
The GitHub workflow has the same inputs and stays switched off.

Pick the environment by running the pipeline from that git branch.
`develop` deploys Databricks `develop`, `ppe` deploys `ppe`, and `main`
deploys `prod`. A feature branch cannot deploy.

## Three names for a model version

| Name | What it means | Who moves it |
|---|---|---|
| Version number, such as `13` | One registered model version. It never moves. | Nothing. It is a pin. |
| `@develop`, `@ppe`, `@prod` | The version that environment last trained. | The train job, only in `train-and-serve`. |
| `@Champion` | The version batch and the endpoint should use when you approve it. | A manual run that types `YES` for `promoteChampion`. |

Do not serve "latest". Latest changes when the next train finishes, including
a bad one. Champion changes only when this run says so.

Train writes the environment alias and stops. It does not move Champion.
A train in `develop` therefore cannot replace the Champion that `prod` is
serving, because those are different Unity Catalog models
(`dbw_iris_ml_dev.develop.iris_species` and `dbw_iris_ml_dev.prod.iris_species`).

## What you select on Run pipeline

| Input | Default | Use it for |
|---|---|---|
| Branch and commit | the branch you click | The environment and the code version |
| `codeVersion` | `HEAD` | Confirms the commit. A SHA must match the commit you selected. |
| `runMode` | `serve` | `serve` deploys that code and points the endpoint. It does not start a job. `train-and-serve` registers a new version, runs infer once, and moves only the env alias. |
| `modelSelector` | `Champion` | `Champion`, `env`, or a number such as `13` |
| `promoteChampion` | `NO` | `YES` points `@Champion` at the version this run serves |
| `confirm` | `NO` | `YES` after `docs/cost-tracker.md` is approved |

`serve` plus `Champion` is the usual manual run: this commit's job
definitions and endpoint, the model version Champion already names, and
no serverless job.

`serve` plus `13` pins version 13. Champion stays where it is unless you
also type `YES`.

`train-and-serve` plus `promoteChampion` `YES` plus `modelSelector` `Champion`
trains, points Champion at the new env-alias version, and serves that version.

Infer loads the same URI, and only when you chose `train-and-serve`.
The endpoint update uses that same version.

## Order

Each later step runs only after the previous one succeeds. Train and infer
are both skipped unless `runMode` is `train-and-serve`. Skipping them does
not block the endpoint update.

1. Confirm `YES`, the branch, and the code version.
2. Read the client secret from Key Vault.
3. Deploy the bundle for that commit. This updates job definitions. It does not start a job.
4. Train only when requested. The job stops after 20 minutes.
5. Infer the selected model URI only when requested. The job stops after 10 minutes.
6. Point `iris-species-<env>` at that version. If it already serves that version, this step does not change the endpoint. Move Champion only on `YES`.

Do not start this pipeline until the cost tracker is approved. `serve` still
updates the endpoint when the served version differs, and an endpoint that
is awake costs money. The first update creates the endpoint. A status read
and the dry-run smoke check do not send a prediction, so they do not wake it.

Each job allows one run. A second click does not queue another run.
