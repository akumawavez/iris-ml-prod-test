"""Guard rails for the Cursor agent hooks and the pre-commit config."""

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins" / "iris-agent" / "scripts"


def _load(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard_shell = _load("guard_shell.py")
guard_read = _load("guard_read.py")
format_python = _load("format_python.py")


def test_force_push_to_develop_is_denied():
    decision = guard_shell.decide_shell("git push --force origin develop")
    assert decision["permission"] == "deny"


def test_force_with_lease_refspec_to_prod_is_denied():
    decision = guard_shell.decide_shell("git push origin +HEAD:prod")
    assert decision["permission"] == "deny"


def test_force_push_of_a_feature_branch_is_allowed():
    decision = guard_shell.decide_shell("git push --force origin feature/local-score")
    assert decision["permission"] == "allow"


def test_ordinary_push_is_allowed():
    decision = guard_shell.decide_shell("git push -u origin cursor/precommit-agent-hooks-3288")
    assert decision["permission"] == "allow"


def test_commit_no_verify_is_denied():
    decision = guard_shell.decide_shell('git commit --no-verify -m "skip hooks"')
    assert decision["permission"] == "deny"


def test_printing_dotenv_is_denied_and_example_is_allowed():
    assert guard_shell.decide_shell("cat .env")["permission"] == "deny"
    assert guard_shell.decide_shell("head -n 20 .env.example")["permission"] == "allow"


def test_secret_files_are_unreadable_and_example_is_readable():
    assert guard_read.decide_read("/workspace/.env")["permission"] == "deny"
    assert guard_read.decide_read("/workspace/certs/workspace.pem")["permission"] == "deny"
    assert guard_read.decide_read("/workspace/.env.example")["permission"] == "allow"


def test_formatter_skips_non_python_and_virtualenv_files(tmp_path: Path):
    notes = tmp_path / "notes.md"
    notes.write_text("hello\n", encoding="utf-8")
    assert format_python.should_format(str(notes), [str(tmp_path)]) is False
    vendored = tmp_path / ".venv" / "lib" / "sample.py"
    vendored.parent.mkdir(parents=True)
    vendored.write_text("x=1\n", encoding="utf-8")
    assert format_python.should_format(str(vendored), [str(tmp_path)]) is False
    source = tmp_path / "sample.py"
    source.write_text("x=1\n", encoding="utf-8")
    assert format_python.should_format(str(source), [str(tmp_path)]) is True
    assert format_python.should_format(str(source), ["/somewhere/else"]) is False


def test_hook_manifests_and_precommit_config_parse():
    project_hooks = json.loads((REPO_ROOT / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
    plugin_hooks = json.loads(
        (REPO_ROOT / "plugins" / "iris-agent" / "hooks" / "hooks.json").read_text(encoding="utf-8")
    )
    plugin = json.loads(
        (REPO_ROOT / "plugins" / "iris-agent" / ".cursor-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
    )
    pre_commit = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert project_hooks["version"] == 1
    assert "beforeShellExecution" in project_hooks["hooks"]
    assert "beforeReadFile" in plugin_hooks["hooks"]
    assert plugin["name"] == "iris-agent"
    assert "ruff-pre-commit" in pre_commit
    assert "rev: v0.16.9" in pre_commit
