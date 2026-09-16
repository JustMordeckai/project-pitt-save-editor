"""Reading and targeted patching of profile.cfg (a Godot ConfigFile)."""
import json
import re


class ProfileError(Exception):
    """Slot or key missing from profile.cfg."""


_SLOT_RE = re.compile(r"^slot_(\d+)=\{(.*?)^\}", re.M | re.S)


def read_slots(text: str) -> dict[int, dict]:
    """Slot summaries keyed by slot number; unreadable blocks are skipped."""
    slots = {}
    for match in _SLOT_RE.finditer(text):
        try:
            slots[int(match.group(1))] = json.loads("{" + match.group(2) + "}")
        except json.JSONDecodeError:
            continue
    return slots


def patch_slot(text: str, slot: int, updates: dict) -> str:
    """Replace only the requested values inside the slot_N block; leave the rest byte for byte."""
    match = next((m for m in _SLOT_RE.finditer(text) if int(m.group(1)) == slot), None)
    if match is None:
        raise ProfileError(f"slot_{slot} not found in profile.cfg")
    body = match.group(2)
    for key, value in updates.items():
        pattern = re.compile(rf'^("{re.escape(key)}": )(.*?)(,?)(\r?)$', re.M)
        if not pattern.search(body):
            raise ProfileError(f"key {key!r} not found in slot_{slot}")
        encoded = json.dumps(value, ensure_ascii=False)
        body = pattern.sub(lambda m: m.group(1) + encoded + m.group(3) + m.group(4), body, count=1)
    return text[:match.start(2)] + body + text[match.end(2):]
