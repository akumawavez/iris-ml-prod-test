## Module 6: What is still switched off

### Teaching Arc
- **Metaphor:** A porch light on a motion sensor. It can turn on when someone arrives, and it turns itself off when the path is empty. Leaving it on all night is the bill. This repo wrote the light’s settings, and left the switch off until a $10 budget is approved.
- **Opening hook:** You have seen the recipe and the paid gate. The last session is the honest inventory: what is written down, what is not live, and how to brief the next agent.
- **Key insight:** The endpoint YAML is real — CPU, size Small, scale-to-zero, a pinned version — and creating it is still a later, human-gated step. Productionalisation here includes knowing what was refused.
- **"Why should I care?":** You can tell an agent “do not POST the endpoint” and “do not add a GPU cluster for 150 rows” because those refusals are already written. The next session should extend the checklist, not invent a second platform.

### Code Snippets (verbatim)

File: databricks/artifacts/iris_endpoint.yml (lines 19-25)

```yaml
        served_entities:
          - name: iris_species
            entity_name: ${var.registered_model_name}
            entity_version: ${var.model_version}
            workload_type: CPU
            workload_size: Small
            scale_to_zero_enabled: true
```

File: databricks.yml (lines 20-22)

```yaml
  model_version:
    description: Served UC model version. Bump after a new version is registered.
    default: "5"
```

### What to show as two columns of cards
Written and waiting (the switch is off):
- Endpoint config: CPU, Small, scale-to-zero, version pin (default "5"), name like `develop-iris-species`
- CD workflows exist and refuse to run unless confirm is YES and the cost tracker is approved
- Teardown notes live in `docs/teardown-and-restore.md` so spend can return to zero
- Issues log: defects are recorded in `issues.md` in the same change that finds or fixes them

Deliberately refused, even if a template includes them:
- A second orchestrator beside Lakeflow Jobs
- Kubernetes or a separate web service for this model
- A GPU or an always-on cluster for a 150-row CPU model
- Putting `bundle deploy` in the test workflow
- Filling a prod host “to see if validate works” before cost approval
- Inference-table capture until the cost sheet lists it (it is a bill)

Later, named so the learner can ask for them:
- Feature tables, a dedicated validation job that sets Challenger, Lakehouse Monitoring, scheduled retrain
- Separate workspaces per environment, including a move to a new region (a region cannot be edited on an existing workspace)

### How to brief the next agent (step cards)
1. Point at `AGENTS.md` and `docs/productionalisation/`.
2. Say which checklist row you want changed.
3. Say the hard stops: no secrets, no deploy inside CI, no CD until the cost tracker is approved, no replacement training unless the task is to update `models/iris_species`.
4. Ask for the same change to update the guide if behavior changes.

### Interactive Elements
- [x] Code↔English on the endpoint YAML (scale to zero and pinned version)
- [x] Quiz — 3 scenarios. (1) The endpoint has been idle for an hour. Why is the expected bill about zero, and what would a live request do to that? (2) An agent wants to serve “latest” so you never edit YAML. Why does this repo pin `entity_version` instead? (3) You want UAE North. Do you edit the current workspace region, or plan a new workspace?
- [x] Callout: scale-to-zero is not “free while someone is calling it.” A warm Small CPU endpoint is about 4 DBU per hour. Idle is the cheap state. A request resets the idle timer.
- [x] Pattern cards for “written,” “refused,” and “later” — three groups.

### Reference Files
- interactive-elements.md → Code ↔ English, Pattern/Feature Cards, Numbered Step Cards, Multiple-Choice Quizzes, Callout Boxes, Glossary Tooltips
- design-system.md → Module Structure
- content-philosophy.md, gotchas.md

### Connections
- **Previous:** Deploy code, not the cake. Infer waits for train. Prod has its own catalog name.
- **Next:** none. End by restating the two-week cadence: three days, then three days. The learner can reopen any nav dot.
- **Tone:** Week 2 day 3 of 3. Warm close, not a lecture. Module id `module-6`, background `var(--color-bg-warm)`. Tooltip: endpoint, scale-to-zero, DBU, version pin, alias, region, issue log. File: `docs/courses/agentic-productionalisation/modules/06-still-off.html`. 4 screens + quiz.
