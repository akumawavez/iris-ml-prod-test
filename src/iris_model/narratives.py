"""Calculation and plain-language text for one scored flower."""

from iris_model.schema import FEATURES


def shap_calculation_narrative(species, base, contributions, probability):
    """State the baseline, each contribution, and the reconstructed probability."""
    parts = [f"For {species}, the baseline probability is {base:.4f}."]
    for feature in FEATURES:
        parts.append(f"{feature} contribution {contributions[feature]:+.4f}.")
    reconstructed = base + sum(contributions[feature] for feature in FEATURES)
    parts.append(
        f"These contributions plus the baseline equal {reconstructed:.4f}, "
        f"matching the predicted probability {probability:.4f}."
    )
    return " ".join(parts)


def shap_layman(species, base, contributions):
    """Name the species and the feature that moved the chance the most."""
    top = max(contributions, key=lambda name: abs(contributions[name]))
    return (
        f"The model began with a {base:.0%} chance of {species} before looking at this flower. "
        f"{top} moved that chance the most. "
        f"That is why this flower is called {species}."
    )


def importance_calculation_narrative(importances):
    """List every impurity importance."""
    parts = ["Impurity importance sums to 1."]
    for feature in FEATURES:
        parts.append(f"{feature}={importances[feature]:.4f}.")
    return " ".join(parts)


def importance_layman(importances):
    """Name the strongest clue on the 150-flower fit."""
    top = max(importances, key=importances.get)
    return (
        f"On the 150 iris flowers used to fit this model, {top} is the strongest clue, "
        f"accounting for {importances[top]:.0%} of the forest's splits."
    )
