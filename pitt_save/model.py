"""Pure editor logic: conversions, validation, and walking the save data."""
import json
import math
import re
from dataclasses import dataclass

from . import catalog

_MILESTONE_SET = frozenset(catalog.MILESTONES)


def format_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def preview(value) -> str:
    if isinstance(value, dict):
        return f"{{{len(value)} key{'s' if len(value) > 1 else ''}}}"
    if isinstance(value, list):
        return f"[{len(value)} item{'s' if len(value) > 1 else ''}]"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return format_value(value)


def type_name(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "text"
    if value is None:
        return "null"
    return "object" if isinstance(value, dict) else "list"


def coerce_like(old, text: str):
    """Convert typed text to the type of the value being replaced."""
    stripped = text.strip()
    if isinstance(old, bool):  # before int: in Python a bool is an int
        lowered = stripped.lower()
        if lowered in ("true", "1"):
            return True
        if lowered in ("false", "0"):
            return False
        raise ValueError("expected a boolean: true or false")
    if isinstance(old, int):
        try:
            return int(stripped)
        except ValueError:
            raise ValueError("expected an integer") from None
    if isinstance(old, float):
        try:
            number = float(stripped)
        except ValueError:
            raise ValueError("expected a number") from None
        if not math.isfinite(number):
            raise ValueError("expected a finite number")
        return number
    if isinstance(old, str):
        return text
    if old is None:
        if stripped.lower() == "null":
            return None
        raise ValueError("only null is accepted here")
    raise ValueError("objects and lists are edited item by item")


def parse_bigint(text: str) -> str:
    stripped = text.strip()
    if not re.fullmatch(r"\d+", stripped):
        raise ValueError("expected a positive integer (digits only)")
    return str(int(stripped))


def parse_count(old, text: str):
    value = coerce_like(old, text)
    if value < 0:
        raise ValueError("expected a positive value")
    return value


def parse_resource(old, text: str):
    return parse_bigint(text) if isinstance(old, str) else parse_count(old, text)


def get_in(data, path: tuple):
    for key in path:
        data = data[key]
    return data


@dataclass
class LevelNode:
    path: tuple[str, ...]              # path from game_state, e.g. ("tools", "box")
    children: list[tuple[str, ...]]    # nested levels, e.g. ("products", "duck", "craft_speed")


def level_nodes(game_state: dict, category: str) -> list[LevelNode]:
    nodes = []
    for name, item in game_state.get(category, {}).items():
        if isinstance(item, dict):
            children = [(category, name, sub) for sub, value in item.items()
                        if isinstance(value, dict) and "level" in value]
            nodes.append(LevelNode((category, name), children))
    return nodes


def milestone_rows(data: dict) -> list[tuple[str, bool]]:
    unlocked = data.get("unlocked_milestones", [])
    have = set(unlocked)
    extras = [name for name in dict.fromkeys(unlocked) if name not in _MILESTONE_SET]
    return [(name, name in have) for name in (*catalog.MILESTONES, *extras)]


def set_milestone(data: dict, name: str, unlocked: bool) -> None:
    milestones = data.setdefault("unlocked_milestones", [])
    if unlocked:
        if name not in milestones:
            milestones.append(name)
    else:
        milestones[:] = [m for m in milestones if m != name]
