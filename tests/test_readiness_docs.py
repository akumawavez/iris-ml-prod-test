"""Readiness pages state an overall percent that matches their steps."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    ROOT / "docs" / "checks" / "mlops-ready.md",
    ROOT / "docs" / "checks" / "databricks-mlops-ready.md",
    ROOT / "docs" / "checks" / "productionalisation-ready.md",
)


def test_each_readiness_page_overall_matches_the_step_mean():
    for path in PAGES:
        text = path.read_text(encoding="utf-8")
        steps = [int(value) for value in re.findall(r"\| (\d+)% \|", text)]
        assert steps, path.name
        overall = round(sum(steps) / len(steps))
        assert f"Overall: {overall}%" in text, path.name
