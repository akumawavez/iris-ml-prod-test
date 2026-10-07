## Module 1: Score a flower

### Teaching Arc
- **Metaphor:** A pressed-flower album. Someone already dried and labeled the specimens. You do not grow a new plant every time you want a name. You open the album and match the measurements.
- **Opening hook:** You already can type four flower measurements and get a species name back, plus two explanations of why.
- **Key insight:** The repo’s first finished thing is a saved model you score locally. Tests load that album. They do not grow a new plant.
- **"Why should I care?":** When you steer an agent, say “score the saved model” instead of “train again.” Training replaces the album. Scoring only looks it up.
- **Cadence:** This is Week 1, day 1 of 3. Show a six-card schedule so the learner sees the two-week plan (three days each week). Do not teach later days in depth.

### Schedule cards (screen 2)
Week 1: Day 1 Score a flower (this module). Day 2 How agents were told. Day 3 The packing list.
Week 2: Day 1 The free lane and the paid gate. Day 2 Ship the recipe. Day 3 What is still switched off.

### Code Snippets (pre-extracted, use verbatim, do not edit)

File: src/iris_model/score.py (lines 1 and 18-26)

```python
"""Load the saved iris model and score rows. This module does not fit."""


def score_model(model_path: Path, rows: list[dict]) -> list[dict]:
    """Score each row with the saved Pyfunc. Do not fit a model here."""
    validate_rows(rows)
    loaded = mlflow.pyfunc.load_model(str(model_path))
    frame = pd.DataFrame(rows).loc[:, list(FEATURES)]
    raw = loaded.predict(frame)
    if isinstance(raw, pd.DataFrame):
        raw = raw.to_dict(orient="records")
    return list(raw)
```

File: src/iris_model/score.py (lines 97-103) — second translation, the four measurements the command requires

```python
    parser.add_argument("--model", default="models/iris_species")
    parser.add_argument("--sepal-length-cm", type=float, required=True)
    parser.add_argument("--sepal-width-cm", type=float, required=True)
    parser.add_argument("--petal-length-cm", type=float, required=True)
    parser.add_argument("--petal-width-cm", type=float, required=True)
```

### Interactive Elements
- [x] **Code↔English translation** — both snippets above, on separate screens
- [x] **Quiz** — 3 scenario questions at the end. (1) A friend asks the agent to “make the answer better” by running train before every score. What should you say instead, and why does that matter for a frozen test? (2) Pytest fails because the species name changed. Do you retrain on the laptop, or look at the saved album and the scoring code? (3) You want the same four measurements checked before any guess. Which idea from this module do you tell the agent to keep: validate the row, or skip checks to be faster?
- [x] **Data flow animation** — actors: You (the measurements), Score (the command), Album (`models/iris_species`), Answer (species plus two narratives). Steps: you type four numbers; score checks the row; score opens the saved album; the album returns a species; the answer adds a calculation story and a plain-language story. No apostrophes in step labels.
- [ ] Group chat — not this module
- [x] **Other** — pattern cards for the six learning days; numbered step cards for “type measurements → check the row → open the album → read the species”

### Reference Files to Read
- `.cursor/skills/codebase-to-course/references/interactive-elements.md` → Code ↔ English Translation Blocks, Message Flow / Data Flow Animation, Multiple-Choice Quizzes, Pattern/Feature Cards, Numbered Step Cards, Callout Boxes, Glossary Tooltips
- `.cursor/skills/codebase-to-course/references/design-system.md` → Module Structure, Syntax Highlighting
- `.cursor/skills/codebase-to-course/references/content-philosophy.md`
- `.cursor/skills/codebase-to-course/references/gotchas.md`

### Connections
- **Previous module:** none. Open by saying what this repo does in one breath: it names an iris from four measurements, and it is built so that naming can later be promoted like software.
- **Next module:** Week 1 day 2, How agents were told — the cue sheet and the door guard that kept agents from training, deploying, or force-pushing.
- **Tone/style notes:** Forest accent already set. Learner is a vibe coder. Tooltip every jargon term on first use in this module: model, score, train, fit, pytest, MLflow, Pyfunc, flag, CLI, feature, narrative, SHAP (say it is one explanation style, do not teach the math). Max 2-3 sentences per text block. Module id `module-1`, background `var(--color-bg)`. File to write: `docs/courses/agentic-productionalisation/modules/01-score-a-flower.html`. Only the `<section class="module">` block. 4 screens plus the quiz screen.
