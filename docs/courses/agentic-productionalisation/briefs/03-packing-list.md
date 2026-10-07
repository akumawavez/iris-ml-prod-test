## Module 3: The packing list

### Teaching Arc
- **Metaphor:** A house-move checklist taped to the door. Boxes are labeled before the van arrives. You do not invent a new box system on the driveway. Productionalisation in this repo is that checklist: folders, required files, workflows, rules, and markdown.
- **Opening hook:** Days 1 and 2 showed a flower scorer and the agent rules. Day 3 is the map of what “done enough to promote” means.
- **Key insight:** Productionalisation here is not “turn on a server.” It is one git repo that already holds code, tests, the bundle description, and the documents a new owner can follow.
- **"Why should I care?":** When you ask an agent to productionalise, name the checklist page, not a vague “make it production ready.”

### Code Snippets (verbatim)

File: src/iris_model/schema.py (lines 1-9)

```python
"""Feature names and the exact scoring error sentences."""

FEATURES = (
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
)
```

Use this to show the contract: training and scoring share one list of measurements. A new column is a contract change.

### What the checklist covers (cards, not a paragraph)
Five pages in `docs/productionalisation/`:
- folder-structure.md — one repo, code and bundle together
- required-files.md — files a reviewer expects before a deploy is allowed
- workflows.md — train, validate, register, deploy, serve, monitor; CI never spends money
- rules.md — branches, secrets, catalogs, cost, what not to click
- markdown-catalog.md — documents a new owner can follow without asking in chat

Status that is already true (badges): packaged Python in `src/iris_model`, lockfile, pytest, ruff, Asset Bundle with develop / ppe / prod targets, test-only CI, gated CD that is not dispatched until the $10 budget is approved.

Status that is later (separate badges, call them later): feature tables, a dedicated validation job, inference tables, Lakehouse Monitoring, scheduled retrain, separate workspaces per environment.

### Interactive Elements
- [x] Code↔English on FEATURES
- [x] Visual file tree of this repo’s minimum homes: `src/iris_model/` scoring and schema, `tests/` load the saved model and do not train, `models/iris_species/` the classroom album, `databricks/` jobs and targets, `docs/` rules and cost, `.github/workflows/` test workflow separate from deploy workflow
- [x] Quiz — 3 architecture questions. (1) An agent offers a second repository just for production YAML. What do you say? (2) Tests that call a live workspace would spend money and need a token. Where should a unit test look instead? (3) You want monitoring tables before the $10 sheet lists them. Which checklist status is that: present, or later?
- [ ] No group chat. No data-flow animation (module 1 owns the flow).
- [x] Pattern cards for the five checklist pages. Callout: Databricks calls this shape MLOps — code, data, and models moving through development, staging, and production with the same review path as software.

### Reference Files
- interactive-elements.md → Visual File Tree, Pattern/Feature Cards, Code ↔ English, Multiple-Choice Quizzes, Permission/Config Badges, Callout Boxes, Glossary Tooltips
- design-system.md → Module Structure
- content-philosophy.md, gotchas.md

### Connections
- **Previous:** Agent cue sheet and door guard.
- **Next:** Week 2 day 1 — the free security lane (CI) versus the paid departure gate (CD).
- **Tone:** Week 1 day 3 of 3. Close the week: you can name a flower, you know how agents are constrained, you can point at the checklist. Module id `module-3`, background `var(--color-bg)`. File: `docs/courses/agentic-productionalisation/modules/03-packing-list.html`. Tooltip: repo, bundle, CI, CD, Unity Catalog, lockfile, schema, YAML, MLOps. 4 screens + quiz.
