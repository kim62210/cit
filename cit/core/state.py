from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from cit.core.paths import get_cit_home


DEFAULT_STATE = {
    "version": 1,
    "activeProfile": None,
    "previousProfile": None,
    "stashStack": [],
    "lastSwitchedAt": None,
}


def ensure_cit_dirs() -> Path:
    base = get_cit_home()
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    (base / "profiles").mkdir(exist_ok=True)
    (base / "stash").mkdir(exist_ok=True)
    return base


def state_path() -> Path:
    return ensure_cit_dirs() / "state.json"


def read_state() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        return DEFAULT_STATE.copy()
    return {**DEFAULT_STATE, **json.loads(path.read_text())}


def write_state(state: dict[str, Any]) -> None:
    path = state_path()
    path.write_text(json.dumps({**DEFAULT_STATE, **state}, indent=2))


def push_stash_id(stash_id: str) -> None:
    state = read_state()
    stack = list(state.get("stashStack", []))
    stack.insert(0, stash_id)
    state["stashStack"] = stack
    write_state(state)


def pop_stash_id(index: int = 0) -> str:
    state = read_state()
    stack = list(state.get("stashStack", []))
    if index >= len(stack):
        raise IndexError("stash index out of range")
    stash_id = stack.pop(index)
    state["stashStack"] = stack
    write_state(state)
    return stash_id


def set_active_profile(name: str | None, previous: str | None = None) -> None:
    state = read_state()
    state["previousProfile"] = previous
    state["activeProfile"] = name
    state["lastSwitchedAt"] = int(time.time() * 1000)
    write_state(state)
