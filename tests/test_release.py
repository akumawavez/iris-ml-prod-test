"""Manual runs select a commit and Champion, the env alias, or one version."""

import pytest

from iris_model.release import assert_code_version, model_uri, resolve_model_selector


def test_champion_is_the_default_alias_and_a_number_pins_a_version():
    assert resolve_model_selector("Champion", "develop") == ("Champion", "")
    assert resolve_model_selector("env", "ppe") == ("ppe", "")
    assert resolve_model_selector("13", "prod") == ("prod", "13")
    assert model_uri("develop", "Champion", "") == (
        "models:/dbw_iris_ml_dev.develop.iris_species@Champion"
    )
    assert model_uri("prod", "prod", "13") == "models:/dbw_iris_ml_dev.prod.iris_species/13"


def test_selector_rejects_latest_and_a_missing_environment():
    with pytest.raises(ValueError):
        resolve_model_selector("latest", "develop")
    with pytest.raises(ValueError):
        resolve_model_selector("env", "")


def test_head_accepts_the_queued_commit_and_a_sha_must_match():
    commit = "abc1234def567890"
    assert assert_code_version("HEAD", commit) == commit
    assert assert_code_version("abc1234", commit) == commit
    with pytest.raises(ValueError):
        assert_code_version("deadbee", commit)
    with pytest.raises(ValueError):
        assert_code_version("main", commit)
