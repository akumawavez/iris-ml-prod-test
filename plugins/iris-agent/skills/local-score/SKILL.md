---
name: local-score
description: Score one iris row from the saved MLflow model and run the local test and lint gate. Use when checking inference output or verifying a Python change before commit.
---

# Local score

The saved model is `models/iris_species`. Pytest loads that model. It does not train.

## Install

```text
uv sync --locked --extra dev
```

## Check

```text
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
```

## Score one row

```text
uv run python -m iris_model.score --model models/iris_species --sepal-length-cm 5.1 --sepal-width-cm 3.5 --petal-length-cm 1.4 --petal-width-cm 0.2
```

Run `uv run python -m iris_model.train` only when the saved model directory should be replaced and committed. Do not deploy a serving endpoint from this skill.
