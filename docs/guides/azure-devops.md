# Azure DevOps guide

CI vs gated CD in plain language: [ELI25: Databricks productionalisation](eli25-databricks-productionalisation.md).

This guide creates the pipeline home for this repo. Follow it when you are ready to click through Azure DevOps. Do not link a subscription, and do not create a Databricks resource, until the cost sheet for that step is approved.

GitHub remains the source repository. Azure Repos is not used.

## What you are building

One Azure DevOps organization and one private project. Later, a pipeline in that project runs when GitHub receives a change.

| Trigger | What the pipeline will do |
|---|---|
| Pull request into `develop`, `ppe`, or `main` | Run tests and `bundle validate`. Do not deploy. Draft pull requests are skipped |
| Push to `feature/*` | Nothing. Open a pull request into `develop` |
| Merge or push to `develop` | Run tests. Deploy stays a manual run of `azure-pipelines-cd.yml` from `develop`, after you type `YES` |
| Push to `ppe` | Run tests, then stop. Deploy is a separate manual run from `ppe` |
| Push to `main` | Run tests, then stop. `main` is the prod branch. A manual CD run from `main` deploys Databricks `prod` |

A manual CD run from any other branch fails before validate spends. Each deploy stage loads only its own variable group (`iris-develop`, `iris-ppe`, or `iris-prod`) and waits on that environment's approval. Two deploys of the same environment queue (`lockBehavior: sequential`).

When the Azure DevOps project can enforce it, require the CI pipeline on `develop`, `ppe`, and `main`, and block direct pushes to those branches. Feature work still enters through a pull request into `develop`.

> **Run only when required.** `azure-pipelines.yml` sets `batch: true` and a
> `paths` filter, so docs-only edits (`docs`, `*.md`) and superseded pushes
> do not consume the 1,800 free Microsoft-hosted minutes. GitHub Actions is
> disabled. Azure DevOps is the only CI/CD.

## 1. Create the organization and project

1. Open [https://dev.azure.com](https://dev.azure.com) and sign in with the Microsoft account you will use for Azure.
2. Create a new organization. The name can match your GitHub user, or be something you will recognize, such as `iris-ml-learning`.
3. Create a private project named `iris-ml-prod-test`.
4. Leave Azure Repos unused. This project exists for Pipelines.

Creating the organization and an empty project is free. Stop here if you only wanted the account in place.

## 2. Connect GitHub

Do this after the GitHub repository exists and you can see `develop`.

1. In the project, open **Project settings** → **Service connections** → **New service connection**.
2. Choose **GitHub**, then authorize the GitHub account that owns `iris-ml-prod-test`.
3. Grant access to that repository only.
4. Name the connection `github-iris-ml-prod-test`.

Official reference: [Build GitHub repositories](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/github).

## 3. Add the pipeline

The pipeline file arrives in the third learning pull request. Until that file is on `develop`, there is nothing to select.

1. **Pipelines** → **New pipeline**.
2. Select **GitHub** and the `github-iris-ml-prod-test` connection.
3. Select the `iris-ml-prod-test` repository.
4. Choose **Existing Azure Pipelines YAML file**.
5. Branch: `develop`. Path: `/azure-pipelines.yml`.
6. Save the pipeline. The first run is tests and `bundle validate` only. It must not deploy or create a workspace.

## 4. Free Microsoft-hosted minutes

A private project gets one free parallel job and 1,800 minutes per month after the organization is linked to an Azure subscription. Each free job can run up to 60 minutes. Source: [Configure and pay for parallel jobs](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs).

Linking billing uses a subscription. Do that only when the cost sheet says to:

1. **Organization settings** → **Billing**.
2. Link the pay-as-you-go subscription.
3. Confirm the Microsoft-hosted parallel job shows the free grant, not a purchased job.
4. Do not buy extra parallel jobs. One job is enough for this repo.

If the free grant does not appear after linking, Microsoft sometimes requires a one-time parallelism request. Use the form linked from that same document. Do not work around it by buying a job.

## 5. Secrets

The Databricks host and client id live in variable group `iris-develop`. The client secret stays in Key Vault `kv-iris-ml-dev-7405`. The pipeline reads it after service connection `sc-iris-keyvault` signs in as `id-iris-ml`. Never put the secret in git, in the YAML, in GitHub, or in a guide.

The variable group is created in the same step as the cost-approved deploy, not in this foundation change.

Which store to use for a new value (Key Vault, bundle variable, job
parameter, GitHub secret, or this variable group) is in
[where-to-put-variables.md](where-to-put-variables.md).
