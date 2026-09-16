"""Disk access: slots, loading, and safe writing of save files."""
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import crypto, profile

GAME_EXE = "projectpitt.exe"
PROFILE_NAME = "profile.cfg"
MAX_SLOTS = 10


class StoreError(Exception):
    """Read/write error meant to be shown to the user."""


@dataclass
class SlotInfo:
    slot: int
    path: Path
    summary: dict


@dataclass
class SaveDocument:
    path: Path
    slot: int
    data: dict


@dataclass
class WriteResult:
    backup_dir: Path
    warning: str | None


def default_save_dir() -> Path:
    return Path(os.environ["APPDATA"]) / "Godot" / "app_userdata" / "Project P.I.T.T"


def slot_save_path(save_dir: Path, slot: int) -> Path:
    return save_dir / ("savegame.save" if slot == 0 else f"savegame_{slot}.save")


def _read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def list_slots(save_dir: Path) -> list[SlotInfo]:
    profile_path = save_dir / PROFILE_NAME
    summaries = profile.read_slots(_read_text(profile_path)) if profile_path.exists() else {}
    return [
        SlotInfo(slot, slot_save_path(save_dir, slot), summaries.get(slot, {}))
        for slot in range(MAX_SLOTS)
        if slot_save_path(save_dir, slot).exists()
    ]


def is_game_running() -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {GAME_EXE}", "/NH"],
        capture_output=True, text=True, errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return GAME_EXE in result.stdout.lower()


def load(path: Path, slot: int) -> SaveDocument:
    try:
        data = json.loads(crypto.decrypt(path.read_bytes()).decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:  # SaveFormatError and JSONDecodeError are ValueErrors
        raise StoreError(f"Cannot read {path.name}: {error}") from error
    if not isinstance(data, dict):
        raise StoreError(f"{path.name} does not contain a JSON object.")
    return SaveDocument(path, slot, data)


def profile_values(data: dict) -> dict:
    """Save values the game mirrors into the slot summary of profile.cfg."""
    game_state = data.get("game_state", {})
    values = {}
    if "money" in game_state:
        values["money"] = game_state["money"]
    if "phase" in data:
        values["phase"] = data["phase"]
    if "total_products" in game_state:
        values["products"] = game_state["total_products"]
    return values


def write(doc: SaveDocument, backup_root: Path,
          game_running: Callable[[], bool] = is_game_running) -> WriteResult:
    if game_running():
        raise StoreError("Project P.I.T.T is running: close the game before saving, "
                         "otherwise its autosave will overwrite your changes.")
    save_dir = doc.path.parent
    profile_path = save_dir / PROFILE_NAME

    backup_dir = backup_root / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_dir.mkdir(parents=True)
    for source in (doc.path, profile_path):
        if source.exists():
            shutil.copy2(source, backup_dir / source.name)

    plain = json.dumps(doc.data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    tmp = doc.path.with_name(doc.path.name + ".tmp")
    tmp.write_bytes(crypto.encrypt(plain))
    try:
        verified = crypto.decrypt(tmp.read_bytes()) == plain
    except crypto.SaveFormatError:
        verified = False
    if not verified:
        tmp.unlink(missing_ok=True)
        raise StoreError("Write verification failed: your original save is untouched.")
    os.replace(tmp, doc.path)

    warning = None
    if profile_path.exists():
        try:
            patched = profile.patch_slot(_read_text(profile_path), doc.slot, profile_values(doc.data))
        except profile.ProfileError as error:
            warning = f"profile.cfg was not updated ({error}): the in-game menu may show stale values."
        else:
            profile_tmp = profile_path.with_name(PROFILE_NAME + ".tmp")
            profile_tmp.write_bytes(patched.encode("utf-8"))
            os.replace(profile_tmp, profile_path)
    return WriteResult(backup_dir, warning)
