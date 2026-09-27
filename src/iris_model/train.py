"""Fit the teaching forest once and save it as an MLflow Pyfunc."""

from pathlib import Path

import joblib
import mlflow.pyfunc
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

from iris_model.schema import FEATURES
from iris_model.score import score_forest

OUTPUT = Path("models/iris_species")


class IrisPyfunc(mlflow.pyfunc.PythonModel):
    """Serve the fitted forest through score_forest."""

    def load_context(self, context):
        self.forest = joblib.load(context.artifacts["forest"])

    def predict(self, context, model_input, params=None):
        rows = model_input.to_dict(orient="records")
        return pd.DataFrame(score_forest(self.forest, rows))


def main():
    bunch = load_iris()
    forest = RandomForestClassifier(n_estimators=100, random_state=42)
    forest.fit(bunch.data, bunch.target)
    forest_path = Path("models") / "forest.joblib"
    forest_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(forest, forest_path)
    if OUTPUT.exists():
        import shutil

        shutil.rmtree(OUTPUT)
    mlflow.pyfunc.save_model(
        path=str(OUTPUT),
        python_model=IrisPyfunc(),
        artifacts={"forest": str(forest_path)},
        pip_requirements=str(Path("requirements.txt")),
    )
    frame = pd.DataFrame([dict(zip(FEATURES, row)) for row in bunch.data])
    loaded = mlflow.pyfunc.load_model(str(OUTPUT))
    loaded.predict(frame.iloc[[0]])
    forest_path.unlink()


if __name__ == "__main__":
    main()
