import json
from pathlib import Path

import pytest

from iris_model.score import score_model

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "iris_species"
SETOSA = {
    "sepal_length_cm": 5.1,
    "sepal_width_cm": 3.5,
    "petal_length_cm": 1.4,
    "petal_width_cm": 0.2,
}
FEATURES = (
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
)


def test_saved_model_returns_input_prediction_and_both_narratives():
    results = score_model(MODEL_PATH, [SETOSA])

    assert len(results) == 1
    row = results[0]
    assert row["input"] == SETOSA
    assert row["prediction"]["species"] == "setosa"
    probabilities = row["prediction"]["probabilities"]
    assert set(probabilities) == {"setosa", "versicolor", "virginica"}
    assert probabilities["setosa"] == max(probabilities.values())
    assert sum(probabilities.values()) == pytest.approx(1.0)

    shap_calc = row["shap"]["calculation"]
    contributions = shap_calc["contributions_for_predicted_species"]
    assert set(contributions) == set(FEATURES)
    reconstructed = shap_calc["base_probability"] + sum(contributions.values())
    assert reconstructed == pytest.approx(probabilities["setosa"], abs=1e-4)
    assert "setosa" in shap_calc["narrative"].lower()
    for feature in FEATURES:
        assert feature in shap_calc["narrative"]
    assert "setosa" in row["shap"]["layman"].lower()

    importance = row["feature_importance"]["calculation"]["importances"]
    assert set(importance) == set(FEATURES)
    assert sum(importance.values()) == pytest.approx(1.0)
    top_feature = max(importance, key=importance.get)
    assert top_feature in row["feature_importance"]["layman"]
    assert "150" in row["feature_importance"]["layman"]
    for feature in FEATURES:
        assert feature in row["feature_importance"]["calculation"]["narrative"]

    json.dumps(results)
