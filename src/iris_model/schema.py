"""Feature names and the exact scoring error sentences."""

FEATURES = (
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
)
SPECIES = ("setosa", "versicolor", "virginica")


def validate_rows(rows: list[dict]) -> None:
    """Raise ValueError when rows is empty or a row breaks the feature contract."""
    if not rows:
        raise ValueError("rows must contain at least one flower")
    for row in rows:
        for feature in FEATURES:
            if feature not in row:
                raise ValueError(f"Missing feature: {feature}")
            value = row[feature]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Feature {feature} must be a number")
        for key in row:
            if key not in FEATURES:
                raise ValueError(f"Unexpected feature: {key}")
