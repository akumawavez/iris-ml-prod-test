## Module 2: How agents were told

### Teaching Arc
- **Metaphor:** A stage manager’s cue sheet, plus a door guard at the wings. The cue sheet (AGENTS.md and rules) tells the performer the order of the show. The door guard (Cursor hooks) stops a dangerous move even if the performer forgets the sheet.
- **Opening hook:** The flower scorer from day 1 did not appear because an agent was free to improvise. The repo wrote down what the agent may do.
- **Key insight:** Agentic coding here means the agent writes the code, but a short instruction file, always-on rules, and hooks decide what it must not do.
- **"Why should I care?":** You steer agents by editing the cue sheet, not by hoping the chat remembers. If a guard blocks you, that block is the production rule speaking.

### Code Snippets (verbatim)

File: plugins/iris-agent/scripts/guard_shell.py (lines 14 and 109-114)

```python
PROTECTED = {"develop", "ppe", "main"}

    if args[0] == "git" and "commit" in args and any(arg in {"-n", "--no-verify"} for arg in args):
        return deny(
            "git commit --no-verify is blocked so pre-commit can run.",
            "Do not pass --no-verify or -n to git commit. "
            "Run `uv run pre-commit run --all-files` and commit again.",
        )
```

File: .cursor/hooks.json (the beforeShellExecution object, lines 5-10)

```json
    "beforeShellExecution": [
      {
        "command": "python3 plugins/iris-agent/scripts/guard_shell.py",
        "timeout": 10,
        "failClosed": false
      }
    ],
```

### Interactive Elements
- [x] **Code↔English** — the Python deny block (primary). Optionally a short second translation of the hook JSON: “before any shell command, run the guard.”
- [x] **Group chat animation** — REQUIRED, unique id `chat-module2`. Actors: You, Agent, Cue sheet (AGENTS.md), Door guard (hook). Message order: You says “force-push main, the history looks messy.” Agent says “the cue sheet says feature branches only, and open a pull request into develop.” Cue sheet says “develop, ppe, and main are protected. Do not skip the checks.” Door guard says “I block force-push and I block commit --no-verify. Pre-commit still runs.” You says “Then I will push the feature branch and ask for review.” No apostrophes if you can avoid them. Use data-sender values actor-you, actor-agent, actor-cue, actor-guard.
- [x] **Quiz** — 3 questions. (1) The agent wants to add `databricks bundle deploy` into the test workflow so “it deploys when tests pass.” What do you tell it, using the cue sheet? (2) A commit is blocked because of `--no-verify`. Is the right move to disable the hook, or to run the checks and commit again? (3) You found a bug. The cue sheet says defects go in issues.md in the same change. Why does that help the next agent?
- [x] **Other** — icon rows for the four instruction layers: AGENTS.md (what to run and what never to do), .cursor/rules/issues-log.mdc (defect log), plugins/iris-agent rules (branches and Python style), hooks (block force-push, secret reads, and format Python after edits). Callout: a rule in a chat disappears; a rule in a file is what the next session reads.

### Reference Files to Read
- interactive-elements.md → Group Chat Animation, Code ↔ English, Multiple-Choice Quizzes, Icon-Label Rows, Callout Boxes, Glossary Tooltips
- design-system.md → Module Structure, Syntax Highlighting
- content-philosophy.md, gotchas.md

### Connections
- **Previous:** Day 1 scored a saved model and was told not to train unless replacing `models/iris_species`.
- **Next:** Day 3 is the packing list — folders and files a reviewer expects before any paid deploy.
- **Tone:** Week 1 day 2 of 3. Module id `module-2`, background `var(--color-bg-warm)`. Tooltip: agent, hook, pull request, force-push, pre-commit, branch, secret, shell. File: `docs/courses/agentic-productionalisation/modules/02-agent-instructions.html`. 4 screens + quiz. Only the section.module block.
