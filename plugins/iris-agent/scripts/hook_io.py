"""Shared stdin/stdout helpers for Cursor command hooks."""

from __future__ import annotations

import json
import sys
from typing import Any


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def allow() -> dict[str, Any]:
    return {"continue": True, "permission": "allow"}


def deny(user_message: str, agent_message: str) -> dict[str, Any]:
    return {
        "continue": True,
        "permission": "deny",
        "user_message": user_message,
        "agent_message": agent_message,
    }


def emit(response: dict[str, Any]) -> None:
    json.dump(response, sys.stdout)
    sys.stdout.write("\n")
