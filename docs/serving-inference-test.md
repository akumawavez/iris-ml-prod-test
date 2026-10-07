# Serving inference test (POST)

How to prove `iris-species-develop` (or `iris-species-ppe` / `iris-species-prod`) answers correctly with one POST, what a good
answer looks like, and what it costs. Auth is environment-variables-only
(`DATABRICKS_HOST`, `DATABRICKS_TOKEN` per `docs/secrets.md`) — never paste a
token into chat, YAML, or this file.

## 0. Try it free first (no endpoint needed)

```powershell
uv run python scripts/test_serving.py --dry-run
```

Validates the exact payload offline and prints the live `curl` equivalent.
No network, no spend. Start here.

## 1. The POST

```powershell
$body = '{"dataframe_split": {"columns": ["sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm"], "data": [[5.1, 3.5, 1.4, 0.2], [6.3, 2.9, 5.6, 1.8]]}}'
curl -X POST "$env:DATABRICKS_HOST/serving-endpoints/iris-species-develop/invocations" `
  -H "Authorization: Bearer $env:DATABRICKS_TOKEN" `
  -H 'Content-Type: application/json' `
  -d $body
```

Python equivalent (or run the script live):

```powershell
$env:DATABRICKS_HOST = 'https://adb-<id>.azuredatabricks.net'   # from your password manager / env
$env:DATABRICKS_TOKEN = 'dap...'                                 # never commit
uv run python scripts/test_serving.py --live
```

## 2. What "correct" looks like

Two rows in, two scored objects out, species in order:

| Row | Measurements (sl, sw, pl, pw) | Expected species |
|---|---|---|
| 1 | 5.1, 3.5, 1.4, 0.2 | **setosa** |
| 2 | 6.3, 2.9, 5.6, 1.8 | **virginica** |

Each object follows the response contract in
`docs/superpowers/specs/2026-09-27-iris-develop-serving-design.md`: echoed
`input`, `prediction.species` + 3-key `probabilities` summing to 1, SHAP
calculation + layman, feature-importance calculation + layman. The served
Pyfunc returns exactly what `score_model` returns locally.

## 3. Recorded LOCAL sample (not a live call)

From `python -m iris_model.score` on the committed `models/iris_species`
(setosa row) — use it to eyeball a live answer:

- `prediction.species`: `setosa`, probabilities `setosa 1.0`
- SHAP: base `0.3334`, contributions `+0.0732 / +0.0025 / +0.2974 / +0.2936`,
  reconstructed `1.0000`
- Layman: "The model began with a 33% chance of setosa … petal_length_cm moved
  that chance the most."
- Importance layman: "On the 150 iris flowers … petal_length_cm is the
  strongest clue, accounting for 44% of the forest's splits."

A live answer should agree on species; probabilities/SHAP values come from the
registered model version, so compare shape and species, not decimals.

## 4. Cost note

Every live call keeps the endpoint warm (up to 4 DBU/h while warm ≈ $0.28/h at
$0.07/DBU). After 30 idle minutes it scales to zero ($0/h). Batch your checks,
then leave it alone — and stamp `docs/cost-tracker.md` with
`./scripts/cost_snapshot.ps1 -UpdateTracker` after testing.

## 5. If the POST fails

| Symptom | Likely cause |
|---|---|
| 401 | Token missing/expired — refresh `DATABRICKS_TOKEN`, never commit it |
| 404 endpoint | Bundle not deployed yet (`databricks bundle deploy -t develop` is gated) |
| 429 / 5xx under load | Small allows 4 concurrent slots — retry once, then check serving logs |
