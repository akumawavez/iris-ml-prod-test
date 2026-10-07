# Cursor best practices, tips, and tricks

Date: 4 October 2026

A working guide for Cursor Desktop: which surface to use, how to brief the agent, and how to keep context, rules, and cost under control. Model choice and Pro pricing live in [cursor-pro-agent-models.md](cursor-pro-agent-models.md).

Primary sources:

- [Best practices for coding with agents](https://cursor.com/blog/agent-best-practices) (Lee Robinson, 9 January 2026)
- [Agent](https://cursor.com/docs/agent/overview), [Plan Mode](https://cursor.com/docs/agent/plan-mode), [Debug Mode](https://cursor.com/docs/agent/debug-mode)
- [Rules](https://cursor.com/docs/context/rules), [Skills](https://cursor.com/docs/context/skills), [Ignore files](https://cursor.com/docs/context/ignore-files)
- [Keyboard shortcuts](https://cursor.com/docs/reference/keyboard-shortcuts)

Shortcuts below are macOS. On Windows and Linux, `Cmd` is `Ctrl`.

## Pick the surface before you type

| You are doing | Use | Why |
| --- | --- | --- |
| Typing the next few lines | **Tab** | Accept with `Tab`, next word with `Cmd+→`, dismiss with `Esc`. Rules do not apply to Tab. |
| One change in the file you are looking at | **Inline Edit** (`Cmd+K`) | One instruction on a selection. User rules do not apply here. |
| A question, no edits | **Ask** | Read-only. Rotate to it with `Shift+Tab` in the agent input. |
| A known, small, multi-file change | **Agent** (`Cmd+I` or `Cmd+L` opens the side panel) | Search, edit, terminal, browser, MCP. |
| A feature, refactor, or anything with more than one reasonable design | **Plan** (`Shift+Tab`) | Research, questions, an editable plan, then build after you approve. |
| A bug you can reproduce and cannot explain from the code | **Debug** (`Shift+Tab`) | Hypotheses, logs, your reproduction, then a small fix from the logs. |

`Cmd+.` opens the mode menu. `Shift+Tab` rotates modes from the chat input. Cursor also suggests Plan when the prompt looks like a large task.

Quick changes you have done many times can go straight to Agent. Everything else starts in Plan.

## Plan, then build

Plan Mode does four things before it writes code:

1. Searches the repo for the files that matter.
2. Asks clarifying questions.
3. Writes a plan with file paths and references.
4. Waits until you approve.

Edit the plan in the markdown it opens. Delete steps you do not want. Add the constraint the agent missed. Click **Save to workspace** to keep the plan in the repo (the blog cites `.cursor/plans/`) so a later chat can resume it.

If the implementation misses the mark, restore the checkpoint, tighten the plan, and run it again. A second pass from a sharper plan is usually cleaner than a chain of “no, I meant…” follow-ups.

## How to brief the agent

Specific prompts finish more often. Compare these:

- Weak: “add tests for auth”
- Strong: “Write a test for the logout edge case in `auth.ts`, using the patterns in `__tests__/`, and do not mock the session store.”

Put four things in the prompt when you have them:

- The outcome.
- The file or symbol, with `@`, when you already know it.
- The pattern to copy (“follow `components/Button.tsx`”).
- How to know it worked (`pytest tests/test_jobs_contract.py`, typecheck, a browser click).

If you do not know the file, leave it untagged. The agent greps and searches the index. Extra irrelevant `@` files pull it toward the wrong place.

Give it a check it can run. Typed code, a linter, and a test are the signals it can use without you in the loop. For test-driven work, say so in stages:

1. Write tests from input/output pairs. Say you are doing TDD so it does not stub the feature.
2. Run the tests and confirm they fail. Say not to write the implementation yet.
3. Commit the tests when you like them.
4. Implement until the tests pass, and say not to edit the tests.
5. Commit the implementation after you have read the diff.

## Context, without stuffing the chat

Tag on purpose:

| Mention | Use it for |
| --- | --- |
| `@` file or folder | You know the exact place |
| `@` a symbol | One function or class |
| `@Branch` | “What am I working on?” or “Review the changes on this branch” |
| `@Past Chats` | A previous thread. The agent reads what it needs. Pasting the whole chat is worse. |
| `@Docs` | A doc set you already added in settings |
| `@Git` | Diff or history |
| `@Terminals` | A failure already on screen |
| A screenshot | Layout, a visual bug, or an error dialog. Paste or drop it. |

Images beat a paragraph when the bug is visual. The agent can also drive the browser, screenshot the app, and check a UI change itself.

While a turn is running:

- `Enter` queues the next instruction until the current task finishes. Drag the queue to reorder.
- `Cmd+Enter` sends now and steers the active turn at the next tool call.
- Pressing Enter twice also steers without cutting off the in-flight tool call.
- `Cmd+Shift+Backspace` cancels generation.

`/side` or `/btw` opens a side chat for a tangent. It keeps its own transcript and can see the parent thread. `@`-mention that side chat later if the main thread needs the answer.

`/goal` sets a standing objective (“fix the flaky tests and get CI green”) instead of treating every message as a new job. Pair it with `/loop` when the work should wake up on an interval. `/goal` is still rolling out; try it in a new chat if it is missing.

Start a **new chat** when the task changes, when the agent repeats the same mistake, or when one unit of work is done. Stay in the chat while you are still iterating on the same feature or debugging what it just built. Long threads accumulate noise after summarization, and the agent starts wandering.

`Cmd+N` or `Cmd+R` starts a new chat. `Cmd+T` opens a chat tab. `Cmd+[` and `Cmd+]` move between chats.

## Watch it, then review

The diff updates as the agent edits. Stop it when the direction is wrong, and say what to do instead.

After it finishes:

- Read the diff. Accept all pending edits with `Cmd+Enter` only after that read. `Cmd+Backspace` rejects them.
- Use **Review → Find Issues** for a line-by-line pass on the proposed edits.
- In Source Control, **Agent Review** compares local changes with the main branch.
- `/review-bugbot` reviews the local diff for likely bugs. On GitHub or GitLab, Bugbot comments on the pull request.
- `/review-security` is a separate pass for auth, injection, secrets, and access control.

Checkpoints are automatic snapshots before large edits. Click one in the timeline to preview, then restore. Restore rolls files back and leaves the messages in the chat. Checkpoints are local and are not commits. Commit when you want history you can push.

For a wide change, ask for a Mermaid diagram of the data flow before you treat the code as done. A bad diagram is a cheap way to see a bad design.

## Rules, skills, and commands

Three layers, used for different jobs:

| Layer | Where | Loaded | Put here |
| --- | --- | --- | --- |
| **Rules** | `.cursor/rules/*.mdc` | At the start of Agent chats, by the rule type | Short facts the agent should follow often: commands, conventions, files to leave alone |
| **AGENTS.md** | Repo root and subfolders | When working in that directory | The same kind of facts, in plain markdown, readable by other agents |
| **Skills** | `.cursor/skills/<name>/SKILL.md` or `.agents/skills/` | When the description matches, or when you type `/name` | Multi-step workflows, scripts, and reference docs |
| **User rules** | Customize → Rules | Every project, Agent only | How you like replies written. Repo conventions belong in the repo. |

Team rules (Team and Enterprise) apply before project rules, which apply before user rules. When two rules conflict, the earlier source wins. Enforced team rules cannot be switched off.

A `.md` file inside `.cursor/rules` is ignored. Project rules use `.mdc` so the frontmatter can set scope. Plain markdown belongs in `AGENTS.md`.

Rule types:

| Frontmatter | When it applies |
| --- | --- |
| `alwaysApply: true` | Every Agent chat. Globs and description are ignored. |
| `alwaysApply: false` and `globs` | When a matching file is in context |
| `alwaysApply: false` and a `description`, no globs | Agent pulls it in when the description matches |
| `alwaysApply: false`, no description, no globs | Only when you `@`-mention the rule |

```markdown
---
description: How to run tests in this repo
alwaysApply: false
globs: "**/*.py"
---

- Run one file: `pytest tests/test_jobs_contract.py`
- After a series of Python edits, run that file before a full suite
- See `tests/test_pipeline_contract.py` for the assertion style
```

Write rules like internal docs:

- Keep each rule under 500 lines, and much shorter if it is always on. Always-on text is paid on every turn.
- One concern per file. Split a grab-bag into composable rules.
- Point at a canonical file with `@filename` instead of pasting the style guide. Pasted copies go stale.
- Add a rule when the agent makes the same mistake twice. Skip the edge case that rarely happens.
- Let the linter own formatting. The agent already knows git, pytest, and npm.
- Commit the rules. `/create-rule` drafts one with the right frontmatter.

Nested `AGENTS.md` files combine with parents. The closer file wins.

Skills stay out of the prompt until they are relevant. Required frontmatter is `name` (must match the folder) and `description` (what it does and when to use it, so the agent can choose it). Optional:

- `paths` limits the skill to matching files. Nested `.cursor/skills/` under a package is already scoped to that directory.
- `disable-model-invocation: true` makes it a slash command: it loads only when you type `/name`.
- `scripts/`, `references/`, and `assets/` hold the long material. Keep `SKILL.md` focused so the agent loads the rest only when it needs it.

A skill can also be a Custom Mode (`Option+Enter` on Mac, `Alt+Enter` on Windows) so it stays in context for the whole session.

Personal skills live in `~/.cursor/skills/`. They stay on your machine unless you turn on **Sync Skills for Cloud Agents** (Settings → Agents). That sync is private to you. Share a skill with the team by publishing it, which is a different step.

`/migrate-to-skills` converts “apply intelligently” rules and old slash commands into skills. Always-on rules, glob rules, and user rules stay where they are.

Commands you run every day can live as markdown in `.cursor/commands/` and show up as `/name`. Useful shapes: `/pr` (diff, commit, push, `gh pr create`), `/fix-issue` (read the issue, patch, open a PR), `/update-deps` (one dependency at a time, tests after each). Check them in.

Built-in skills you can type today include `/create-rule`, `/create-skill`, `/create-hook`, `/create-subagent`, `/loop`, `/review`, `/review-bugbot`, `/review-security`, `/split-to-prs`, and `/automate`.

## Hooks and MCP, lightly

Hooks in `.cursor/hooks.json` (shared) or `~/.cursor/hooks.json` (personal) run a script around agent actions. Use a narrow event: format after an edit, block a secret in the prompt, or gate a shell command. A `stop` hook can send a follow-up so the agent keeps going until a check passes, with a max iteration count so it cannot loop forever. See the [hooks docs](https://cursor.com/docs/hooks).

MCP connects the agent to tools you already use (issue trackers, logs, browsers, databases). Project config is `.cursor/mcp.json`. Keep secrets in the environment, not in the JSON you commit. `.cursorignore` does not apply to what a terminal command or an MCP server can read, so ignore files are not a lock on those tools.

## Parallel agents and cloud agents

Local agents can run in separate git worktrees so they do not edit the same files. Pick the worktree option from the agent dropdown. When one finishes, **Apply** merges it back.

For a hard problem, run the same prompt on more than one model and compare. Cursor will mark the candidate it prefers. Turn on notifications so you notice when a background run finishes.

Cloud agents fit work you would otherwise queue for later: a bug that appeared mid-task, tests for code you just merged, a doc update, a small refactor. Start them from the editor, [cursor.com/agents](https://cursor.com/agents), Slack (`@Cursor`), or a phone. They clone the repo, work on a branch, and open a pull request. Use a local agent when the task needs your machine’s credentials, data, or a tight edit loop.

## Index, secrets, and ignore files

Cursor indexes the repo for semantic search and respects `.gitignore`. It also skips lockfiles, `node_modules/`, `.venv/`, media, archives, and `.env*` by default.

Add a root `.cursorignore` (gitignore syntax) for anything else the agent, Tab, and Inline Edit should not read, and that `@` mentions should not open:

```gitignore
# credentials
**/.env
**/.env.*
**/credentials.json
**/*.pem
**/*.key
```

You can set the same patterns globally so every project ignores env files and keys. Hierarchical ignore (search parent directories) is under Cursor Settings → Indexing → Ignore Files.

Ignoring a secret file reduces exposure. It is not a guarantee. Keep real secrets out of prompts, rules, `AGENTS.md`, skills, and `mcp.json`.

A negation (`!path`) cannot bring back a file inside a directory that was ignored as a whole. Ignore the nested directory, then negate the file.

`*.csv` is on the default ignore list. If this repo’s agent needs a sample CSV, negate that specific file in `.cursorignore`.

## Models and cost

Pick the model in the picker. **Auto** can route the request to a third-party model and bill that model’s price.

On the $20 Pro plan, the practical split in [cursor-pro-agent-models.md](cursor-pro-agent-models.md) is:

- Daily agent work: **Composer 2.5**, normal speed.
- A chat that stalls: switch that chat to **Grok 4.7**, normal speed, then switch back.
- Leave **Fast** variants off. They burn the allowance several times faster.

`Cmd+/` cycles models. Max Mode enlarges the context window and the bill. Turn it on for one large task, then turn it off.

## Keyboard cheatsheet

Open the full list with `Cmd+R` then `Cmd+S`, or search “Keyboard Shortcuts” in the command palette (`Cmd+Shift+P`).

| Action | Shortcut |
| --- | --- |
| Toggle the side panel | `Cmd+I` or `Cmd+L` |
| Toggle Agent layout | `Cmd+E` |
| Mode menu | `Cmd+.` |
| Rotate Agent / Plan / Ask / Debug | `Shift+Tab` in the input |
| Inline edit | `Cmd+K` in the editor |
| Search conversations (Agents Window) | `Cmd+K` |
| Find in the open chat | `Cmd+F` |
| Cycle models | `Cmd+/` |
| Cursor settings | `Cmd+Shift+J` |
| Add selection as context | `Cmd+Shift+L` |
| Queue a message while the agent works | `Enter` |
| Send immediately / accept all edits | `Cmd+Enter` |
| Reject all edits | `Cmd+Backspace` |
| Cancel generation | `Cmd+Shift+Backspace` |
| New chat | `Cmd+N` or `Cmd+R` |
| Accept Tab suggestion | `Tab` |
| Accept next word | `Cmd+→` |
| Voice mode | `Cmd+Shift+Space` |

`Cmd+K` depends on focus: inline edit in the editor, conversation search in the Agents Window.

## Habits that hold up

- Plan the change that touches many files or has two plausible designs.
- Name the file when you know it. Let search work when you do not.
- One task per chat. `@Past Chats` when the next task needs the last one.
- Point at a canonical file. Keep always-on rules short.
- Put procedures in skills. Put repeated prompts in `/` commands.
- Require a check: a test, a typecheck, or a screenshot.
- Read the diff before `Cmd+Enter`.
- Use Debug when you can reproduce the bug and Agent is guessing.
- Restore a checkpoint and re-run the plan when the build went the wrong way.
- Pick Composer 2.5 yourself. Leave Fast and Max off unless this task needs them.

## Sources

- https://cursor.com/blog/agent-best-practices
- https://cursor.com/docs/agent/overview
- https://cursor.com/docs/agent/plan-mode
- https://cursor.com/docs/agent/debug-mode
- https://cursor.com/docs/context/rules
- https://cursor.com/docs/context/skills
- https://cursor.com/docs/context/ignore-files
- https://cursor.com/docs/reference/keyboard-shortcuts
- https://cursor.com/docs/cli/using
- https://cursor.com/docs/models-and-pricing
