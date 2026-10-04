#!/usr/bin/env python3
"""Block force-pushes to protected branches, hook bypasses, and secret-file reads."""

from __future__ import annotations

import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_io import allow, deny, emit, load_payload  # noqa: E402

PROTECTED = {"develop", "ppe", "prod"}
READ_COMMANDS = {"cat", "head", "tail", "less", "more", "bat", "type", "gc", "get-content"}
FORCE_FLAGS = {"-f", "--force", "--force-with-lease", "--force-if-includes"}
OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "-o",
    "--push-option",
    "--receive-pack",
    "--exec",
    "--repo",
}


def _is_secret_name(name: str) -> bool:
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return True
    return name.endswith(".pem") or name.endswith(".key")


def _flag_name(arg: str) -> str:
    return arg.split("=", 1)[0]


def _protected_ref(token: str) -> str | None:
    ref = token.lstrip("+")
    if ":" in ref:
        ref = ref.split(":", 1)[1]
    ref = ref.removeprefix("refs/heads/")
    if ref.startswith("origin/"):
        ref = ref[len("origin/") :]
    if ref in PROTECTED:
        return ref
    return None


def _is_force(args: list[str]) -> bool:
    for arg in args:
        if _flag_name(arg) in FORCE_FLAGS:
            return True
        if arg.startswith("+") and not arg.startswith("++"):
            return True
    return False


def _push_refs(args: list[str]) -> list[str] | None:
    try:
        index = args.index("push")
    except ValueError:
        return None
    index += 1
    positional: list[str] = []
    while index < len(args):
        arg = args[index]
        if arg in OPTIONS_WITH_VALUE:
            index += 2
            continue
        if arg.startswith("-"):
            index += 1
            continue
        positional.append(arg)
        index += 1
    if positional and _looks_like_remote(positional[0]):
        return positional[1:]
    return positional


def _looks_like_remote(token: str) -> bool:
    if token in {"origin", "upstream"}:
        return True
    return "://" in token or token.startswith("git@")


def _reads_secret(args: list[str]) -> bool:
    saw_reader = False
    for arg in args:
        base = arg.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if base in READ_COMMANDS:
            saw_reader = True
            continue
        if saw_reader and not arg.startswith("-") and _is_secret_name(Path(arg).name):
            return True
    return False


def decide_shell(command: str) -> dict[str, object]:
    try:
        args = shlex.split(command)
    except ValueError:
        return allow()
    if not args:
        return allow()

    if args[0] == "git" and "commit" in args and any(arg in {"-n", "--no-verify"} for arg in args):
        return deny(
            "git commit --no-verify is blocked so pre-commit can run.",
            "Do not pass --no-verify or -n to git commit. "
            "Run `uv run pre-commit run --all-files` and commit again.",
        )

    if args[0] == "git" and _is_force(args):
        refs = _push_refs(args)
        if refs is not None:
            protected = [name for name in (_protected_ref(ref) for ref in refs) if name]
            if protected or not refs:
                target = protected[0] if protected else "the current upstream"
                return deny(
                    f"Force-push to {target} is blocked.",
                    "docs/branch-rules.md forbids force-pushing develop, ppe, and prod. "
                    "Push a feature branch and open a pull request.",
                )

    if _reads_secret(args):
        return deny(
            "Reading a secret file in the shell is blocked.",
            "Do not cat, head, or otherwise print .env, .pem, or .key files. "
            "Use .env.example for names only.",
        )

    return allow()


def main() -> None:
    payload = load_payload()
    command = payload.get("command")
    if not isinstance(command, str):
        emit(allow())
        return
    emit(decide_shell(command))


if __name__ == "__main__":
    main()
