"""What a manual CI/CD run is allowed to select.

The environment still comes from the git branch. The commit you queue is
the code version. Champion is the approved model alias. A version number
pins one model version and does not mean "latest".
"""

from __future__ import annotations

from iris_model.identities import CATALOG


def resolve_model_selector(selector: str, env_suffix: str) -> tuple[str, str]:
    """Return (alias, version). Version is empty when the alias should be read."""
    value = selector.strip()
    lowered = value.lower()
    if lowered == "champion":
        return "Champion", ""
    if lowered == "env":
        if not env_suffix.strip():
            raise ValueError("env suffix is required when modelSelector is env")
        return env_suffix.strip(), ""
    if value.isdigit() and int(value) > 0:
        if not env_suffix.strip():
            raise ValueError("env suffix is required when pinning a model version")
        return env_suffix.strip(), str(int(value))
    raise ValueError("modelSelector must be Champion, env, or a version number")


def model_uri(env_suffix: str, alias: str, version: str) -> str:
    """Unity Catalog URI for the alias, or for one numeric version."""
    name = f"{CATALOG}.{env_suffix}.iris_species"
    if version:
        return f"models:/{name}/{version}"
    return f"models:/{name}@{alias}"


def assert_code_version(expected: str, actual: str) -> str:
    """Return the queued commit. HEAD accepts it. A SHA must match that commit."""
    wanted = expected.strip()
    got = actual.strip()
    if wanted.upper() in {"", "HEAD"}:
        if not got:
            raise ValueError("the queued commit is empty")
        return got
    if len(wanted) < 7 or any(char not in "0123456789abcdefABCDEF" for char in wanted):
        raise ValueError("codeVersion must be HEAD or a git SHA of at least 7 hex characters")
    if not got.lower().startswith(wanted.lower()):
        raise ValueError(f"queued commit {got} does not match codeVersion {wanted}")
    return got
