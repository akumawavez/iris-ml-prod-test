---
name: check
description: Run pytest, ruff, and pre-commit without deploying
---

# Check

From the repository root:

1. `uv sync --locked --extra dev`
2. `uv run pytest -q`
3. `uv run ruff check .`
4. `uv run ruff format --check .`
5. `uv run pre-commit run --all-files`

Report the first failing command and its output. Do not run `databricks bundle deploy`.
