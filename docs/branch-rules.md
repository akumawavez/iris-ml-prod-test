# Branch rules

Promotion is one path:

`feature/<short-name>` → `develop` → `ppe` → `main`

`main` is the prod branch. There is no git branch named `prod`. The Databricks environment for `main` is still named `prod`.

`develop` stays the default branch. Nothing deploys until the cost sheet is approved. Gated CD is manual.

## Rules we follow

- Work happens on `feature/<short-name>` branches cut from `develop`.
- A feature pull request merges only into `develop`.
- `develop` promotes into `ppe` only through a pull request.
- `ppe` promotes into `main` only through a pull request. That merge is the prod release.
- Do not force-push `develop`, `ppe`, or `main`.
- Do not commit secrets. Credentials belong in Azure DevOps secret variables or a local `.env` file, both ignored by git.

## Git branch and Databricks environment

| Git branch | Databricks target | Env prefix, alias, endpoint |
|---|---|---|
| `feature/*` | none | no deploy |
| `develop` | `develop` | `develop-iris-species` |
| `ppe` | `ppe` | `ppe-iris-species` |
| `main` (prod branch) | `prod` | `prod-iris-species` |

Each target records that pair in `variables.git_branch` under `databricks/targets/`. CD deploys a target only from its git branch: `develop` from `develop`, `ppe` from `ppe`, and `prod` from `main`.

## What GitHub Free can enforce

Protected branches on a private repository require GitHub Pro, GitHub Team, or GitHub Enterprise. On GitHub Free they are available for public repositories. Official reference: [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

This repo stays private. The rules above are the working agreement. When the account can enforce them, apply this protection to `develop`, `ppe`, and `main`:

1. Repository **Settings** → **Branches** → **Add branch ruleset** (or classic branch protection).
2. Require a pull request before merging.
3. Block force pushes and branch deletion.
4. Do not add required status checks. CI already runs on pull requests into `develop`, `ppe`, and `main`.

## Branches

| Branch | Role |
|---|---|
| `feature/*` | One change, opened as a pull request into `develop` |
| `develop` | Integration branch. Databricks env `develop` |
| `ppe` | Pre-production. Databricks env `ppe`. Reached only from `develop` |
| `main` | Prod branch. Databricks env `prod`. Reached only from `ppe` |
