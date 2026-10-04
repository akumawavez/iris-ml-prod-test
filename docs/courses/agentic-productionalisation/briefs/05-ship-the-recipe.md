## Module 5: Ship the recipe, refit there

### Teaching Arc
- **Metaphor:** A recipe card versus a finished cake. You mail the recipe to three kitchens (develop, ppe, prod). Each kitchen bakes its own cake. You do not mail one cake and hope it survives the trip. Databricks’ phrase for this is “deploy code, not models.”
- **Opening hook:** Day 1 of this week showed the paid gate. Day 2 is what would pass through that gate: a job description, not the laptop’s saved flower album.
- **Key insight:** The same git commit can train in each environment and register a new Unity Catalog version there. The laptop folder `models/iris_species` is the classroom copy for pytest. The endpoint, when it exists, serves the catalog version named in the target.
- **"Why should I care?":** If an agent says “copy the model file into prod,” you can answer “register a new version by running the training code in that environment.”

### Code Snippets (verbatim)

File: databricks/jobs/iris_ml_job_pipeline.yml (lines 19-42)

```yaml
        - task_key: train
          spark_python_task:
            python_file: ../../notebooks/train_register.py
            parameters:
              - --experiment
              - ${var.experiment_name}
              - --tracking-uri
              - databricks
              - --registered-name
              - ${var.registered_model_name}
              - --register
              - --alias
              - ${var.model_alias}
              - --env
              - ${var.env}
          environment_key: default
        - task_key: infer
          depends_on:
            - task_key: train
          spark_python_task:
            python_file: ../../notebooks/infer.py
```

File: databricks/targets/prod.yml (lines 1-14) — show that prod is a target, git branch main, its own model name

```yaml
targets:
  prod:
    mode: production
    workspace:
      host: https://adb-7405619226406985.5.azuredatabricks.net
      root_path: /Shared/.bundle/${bundle.name}/${bundle.target}
    variables:
      env: prod
      git_branch: main
      env_prefix: prod
      registered_model_name: dbw_iris_ml_dev.prod.iris_species
      model_alias: prod
```

Prefer the train/infer YAML as the code↔English hero (it is long — translate the meaningful lines: task train, register, alias, then infer depends_on train). You may shorten the English side to one line per idea, but the code side must stay exact. If 20 lines is too tall, use only lines 31-39 (infer depends_on train) as the translation and put the register parameters in badges.

### Facts
- Bundle file `databricks.yml` includes `databricks/jobs/*.yml` and `databricks/targets/*.yml`. The serving endpoint YAML is not applied by bundle deploy, because waiting on the container blocked the job. CD creates the endpoint separately, and only after approval.
- One catalog `dbw_iris_ml_dev`, schemas develop, ppe, and prod. Three-level name catalog.schema.model.
- Aliases: environment alias (`develop`, `ppe`, `prod`) says which version that environment trained. Challenger means passed validation. Champion means this is what batch loads. Those alias-update tasks are not all built yet — say that honestly.
- Infer does not run if train fails, because of depends_on.
- All three targets share one workspace host today. Separate workspaces are later.

### Interactive Elements
- [x] Code↔English on the depends_on / train task idea, code exact
- [x] Three pattern cards: develop kitchen, ppe kitchen, prod kitchen — same recipe, different catalog schema and endpoint name (`develop-iris-species` vs `prod-iris-species`)
- [x] Quiz — 3 questions. (1) Pytest on a laptop fails. Should the agent copy `models/iris_species` into the prod catalog to “fix” it? (2) Train fails. Should infer still score yesterday’s version inside this job? What does depends_on decide? (3) You want prod to serve whatever was registered last in develop. Why does this repo pin a version and a per-environment name instead?
- [x] Callout: copying weights across catalogs is the exception and needs a written reason (an ADR). This teaching repo keeps a frozen album in git only so laptop tests have an input.

### Reference Files
- interactive-elements.md → Code ↔ English, Pattern/Feature Cards, Multiple-Choice Quizzes, Callout Boxes, Glossary Tooltips, Icon-Label Rows
- design-system.md → Module Structure
- content-philosophy.md, gotchas.md

### Connections
- **Previous:** CI is free, CD is the paid gate, prod deploys from git branch main.
- **Next:** Day 3 — the endpoint exists as YAML with scale-to-zero and a pinned version, but it is deliberately not switched on, and several production pieces are still “later.”
- **Tone:** Week 2 day 2 of 3. Module id `module-5`, background `var(--color-bg)`. Tooltip: bundle, job, task, Unity Catalog, alias, register, schema, catalog, ADR, serverless. Do not invent secret values. The workspace host in the snippet is already in the repo; you may show it because it is committed. File: `docs/courses/agentic-productionalisation/modules/05-ship-the-recipe.html`. 4 screens + quiz.
