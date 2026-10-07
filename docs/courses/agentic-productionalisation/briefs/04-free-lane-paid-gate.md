## Module 4: The free lane and the paid gate

### Teaching Arc
- **Metaphor:** An airport. The security lane (CI) scans your bag and costs you nothing but time. The departure gate (CD) is where the plane actually leaves, and that flight burns fuel. You do not board by accident because your bag was scanned.
- **Opening hook:** Week 1 ended with a packing list. Week 2 day 1 is how a change is allowed to move, and where money starts.
- **Key insight:** Promotion is `feature/*` → `develop` → `ppe` → `main`. `main` is the prod git branch and selects Databricks target `prod`. CI tests. CD deploys, only when a human types YES, and only after the cost tracker is approved.
- **"Why should I care?":** The most expensive agent mistake is putting deploy inside the test workflow. You can spot that in a YAML trigger block.

### Code Snippets (verbatim)

File: .github/workflows/cd.yml (lines 15-26 and 41-52)

```yaml
on:
  workflow_dispatch:
    inputs:
      confirm:
        description: "Type YES to confirm the $10 budget is active"
        required: true
        default: "NO"
      target:
        description: Databricks target. prod deploys only from git branch main
        type: choice
        options: [develop, ppe, prod]
        default: develop
```

```yaml
      - name: Refuse unless explicitly confirmed
        run: |
          test "${{ inputs.confirm }}" = "YES"
      - name: Match git branch to Databricks target
        run: |
          case "${{ inputs.target }}" in
            develop) expected=develop ;;
            ppe) expected=ppe ;;
            prod) expected=main ;;
            *) echo "unknown target ${{ inputs.target }}" >&2; exit 1 ;;
          esac
          test "${GITHUB_REF_NAME}" = "$expected"
```

### Facts to show as badges, not prose
- GitHub Actions is disabled. `.github/workflows/ci.yml` and `cd.yml` do not run on pull request or push. Every job is `if: false`.
- `azure-pipelines.yml` is the only CI. It tests and runs `databricks bundle validate`. Validate reads the description. It does not create jobs.
- `azure-pipelines-cd.yml` is the only CD. It does not run on push (`trigger: none`).
- Cap on this project: $10 per month. Do not deploy, run a job, or POST the endpoint until `docs/cost-tracker.md` is approved.
- `databricks bundle validate` is free. `databricks bundle deploy` and `databricks bundle run` are not.

### Interactive Elements
- [x] Code↔English — translate the confirm YES block and the branch match (develop↔develop, ppe↔ppe, prod↔main). Two translation blocks is fine if each stays short; or one translation of the case statement only if the screen gets crowded. Prefer the case statement as the hero translation.
- [x] Flow diagram (static `.flow-steps`, not the animated `.flow-animation` — module 1 owns that): feature branch → pull request into develop → CI tests → human merges → optional gated CD. Mark CI as free and CD as paid.
- [x] Quiz — 3 scenarios. (1) Tests are green on a docs typo. Should CI have run? Use the path filter idea. (2) Someone dispatches CD with confirm left as NO, from branch develop, target prod. Which of the two checks fails, and what is the right branch for prod? (3) An agent says “validate is basically deploy.” What do you correct?
- [x] Callout: a red test should be free. If fixing a test can create a cloud bill, the lanes are crossed.

### Reference Files
- interactive-elements.md → Code ↔ English, Flow Diagrams, Permission/Config Badges, Multiple-Choice Quizzes, Callout Boxes, Glossary Tooltips, Numbered Step Cards
- design-system.md → Module Structure
- content-philosophy.md, gotchas.md

### Connections
- **Previous:** The packing list. CI and CD are two different workflows on that list.
- **Next:** Day 2 ships the recipe (the bundle job) into each environment and refits there, instead of copying the flower album from a laptop into production.
- **Tone:** Week 2 day 1 of 3. Say that out loud in the header. Module id `module-4`, background `var(--color-bg-warm)`. Tooltip: pull request, CI, CD, workflow, validate, deploy, target, branch, budget. File: `docs/courses/agentic-productionalisation/modules/04-free-lane-paid-gate.html`. 4 screens + quiz.
