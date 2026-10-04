# iris-agent

Cursor plugin for this repository. It packages the branch and secret rules, a local score skill, a check command, an MLOps review agent, and the same command hooks that `.cursor/hooks.json` loads for cloud agents.

## What the hooks do

- `beforeShellExecution` blocks force-pushes to `develop`, `ppe`, and `prod`, blocks `git commit --no-verify`, and blocks shell commands that print `.env`, `.pem`, or `.key` files.
- `beforeReadFile` blocks those same secret files from entering the agent context. `.env.example` stays readable.
- `afterFileEdit` runs `uv run ruff format` and `uv run ruff check --fix` on Python files inside the workspace. A missing `uv` or a ruff failure does not block the edit.

Project hooks in `.cursor/hooks.json` call `plugins/iris-agent/scripts/`. The plugin copy in `hooks/hooks.json` calls `./scripts/` so an installed plugin can find them.

## Install

This repo also lists the plugin in `.cursor-plugin/marketplace.json`. From Cursor, add the repository marketplace and enable **Iris MLOps agent**. Project hooks load in a trusted workspace without that install.

Pre-commit is separate. Install it with `uv run pre-commit install`.
