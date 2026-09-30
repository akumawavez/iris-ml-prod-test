from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVING_REQUIREMENTS = ROOT / "requirements-serving.txt"


def test_registered_model_uses_linux_compatible_runtime_requirements():
    requirements = SERVING_REQUIREMENTS.read_text(encoding="utf-8").lower()
    training_script = (ROOT / "notebooks" / "train_register.py").read_text(encoding="utf-8")
    local_trainer = (ROOT / "src" / "iris_model" / "train.py").read_text(encoding="utf-8")

    assert "pywin32" not in requirements
    assert "pytest" not in requirements
    assert "scikit-learn" in requirements
    assert "shap" in requirements
    assert "pip_requirements=str(SERVING_REQUIREMENTS)" in training_script
    assert 'pip_requirements="requirements-serving.txt"' in local_trainer
