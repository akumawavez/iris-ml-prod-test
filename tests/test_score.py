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


VIRGINICA = {
    "sepal_length_cm": 6.3,
    "sepal_width_cm": 2.9,
    "petal_length_cm": 5.6,
    "petal_width_cm": 1.8,
}


def test_saved_model_scores_each_row_separately():
    results = score_model(MODEL_PATH, [SETOSA, VIRGINICA])
    assert [row["prediction"]["species"] for row in results] == ["setosa", "virginica"]
    assert results[0]["input"] == SETOSA
    assert results[1]["input"] == VIRGINICA
    assert results[0]["feature_importance"] == results[1]["feature_importance"]


def test_empty_rows_are_rejected():
    with pytest.raises(ValueError, match="rows must contain at least one flower"):
        score_model(MODEL_PATH, [])


def test_missing_feature_names_the_feature():
    incomplete = dict(SETOSA)
    del incomplete["petal_width_cm"]
    with pytest.raises(ValueError, match="Missing feature: petal_width_cm"):
        score_model(MODEL_PATH, [incomplete])


def test_non_numeric_feature_is_rejected():
    bad = dict(SETOSA)
    bad["petal_length_cm"] = "long"
    with pytest.raises(ValueError, match="Feature petal_length_cm must be a number"):
        score_model(MODEL_PATH, [bad])


def test_bool_is_not_a_number():
    bad = dict(SETOSA)
    bad["sepal_length_cm"] = True
    with pytest.raises(ValueError, match="Feature sepal_length_cm must be a number"):
        score_model(MODEL_PATH, [bad])


def test_unexpected_feature_is_rejected():
    extra = dict(SETOSA)
    extra["flower_id"] = 1
    with pytest.raises(ValueError, match="Unexpected feature: flower_id"):
        score_model(MODEL_PATH, [extra])
