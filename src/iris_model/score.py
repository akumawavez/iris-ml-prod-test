"""Load the saved iris model and score rows. This module does not fit."""

from pathlib import Path

import mlflow.pyfunc
import pandas as pd
import shap

from iris_model.narratives import (
    importance_calculation_narrative,
    importance_layman,
    shap_calculation_narrative,
    shap_layman,
)
from iris_model.schema import FEATURES, SPECIES, validate_rows


def score_model(model_path: Path, rows: list[dict]) -> list[dict]:
    """Score each row with the saved Pyfunc. Do not fit a model here."""
    validate_rows(rows)
    loaded = mlflow.pyfunc.load_model(str(model_path))
    frame = pd.DataFrame(rows).loc[:, list(FEATURES)]
    raw = loaded.predict(frame)
    if isinstance(raw, pd.DataFrame):
        raw = raw.to_dict(orient="records")
    return list(raw)


def score_forest(forest, rows: list[dict]) -> list[dict]:
    """Build the response contract from an already fitted forest."""
    validate_rows(rows)
    frame = pd.DataFrame(rows).loc[:, list(FEATURES)]
    probabilities = forest.predict_proba(frame)
    class_names = [SPECIES[int(label)] for label in forest.classes_]
    explainer = shap.TreeExplainer(forest)
    importances = {
        feature: float(forest.feature_importances_[index])
        for index, feature in enumerate(FEATURES)
    }
    importance_narrative = importance_calculation_narrative(importances)
    importance_plain = importance_layman(importances)
    results = []
    for row_index, row in enumerate(rows):
        probs = {
            species: float(probabilities[row_index, class_names.index(species)])
            for species in SPECIES
        }
        species = max(probs, key=probs.get)
        class_index = class_names.index(species)
        base, contributions = _contributions(explainer, frame.iloc[[row_index]], class_index)
        results.append(
            {
                "input": {feature: float(row[feature]) for feature in FEATURES},
                "prediction": {"species": species, "probabilities": probs},
                "shap": {
                    "calculation": {
                        "base_probability": base,
                        "contributions_for_predicted_species": contributions,
                        "narrative": shap_calculation_narrative(
                            species, base, contributions, probs[species]
                        ),
                    },
                    "layman": shap_layman(species, base, contributions),
                },
                "feature_importance": {
                    "calculation": {
                        "importances": importances,
                        "narrative": importance_narrative,
                    },
                    "layman": importance_plain,
                },
            }
        )
    return results


def _contributions(explainer, frame, class_index):
    explanation = explainer(frame)
    values = explanation.values
    base_values = explanation.base_values
    if getattr(values, "ndim", 1) == 3:
        contrib = values[0, :, class_index]
        base = float(base_values[0, class_index])
    else:
        contrib = values[0]
        base = float(base_values[0])
    contributions = {
        feature: float(contrib[index]) for index, feature in enumerate(FEATURES)
    }
    return base, contributions


def _cli():
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/iris_species")
    parser.add_argument("--sepal-length-cm", type=float, required=True)
    parser.add_argument("--sepal-width-cm", type=float, required=True)
    parser.add_argument("--petal-length-cm", type=float, required=True)
    parser.add_argument("--petal-width-cm", type=float, required=True)
    args = parser.parse_args()
    row = {
        "sepal_length_cm": args.sepal_length_cm,
        "sepal_width_cm": args.sepal_width_cm,
        "petal_length_cm": args.petal_length_cm,
        "petal_width_cm": args.petal_width_cm,
    }
    print(json.dumps(score_model(Path(args.model), [row]), indent=2))


if __name__ == "__main__":
    _cli()
