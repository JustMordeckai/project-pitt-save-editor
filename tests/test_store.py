import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pitt_save import crypto, profile, store


def test_slot_save_path():
    base = Path("x")
    assert store.slot_save_path(base, 0) == base / "savegame.save"
    assert store.slot_save_path(base, 3) == base / "savegame_3.save"


def test_list_slots_with_profile_summary(save_dir):
    slots = store.list_slots(save_dir)
    assert [s.slot for s in slots] == [0]
    assert slots[0].path == save_dir / "savegame.save"
    assert slots[0].summary["money"] == "6"


def test_list_slots_without_profile(save_dir):
    (save_dir / "profile.cfg").unlink()
    assert store.list_slots(save_dir)[0].summary == {}


def test_load(save_dir):
    doc = store.load(save_dir / "savegame.save", 0)
    assert doc.slot == 0
    assert doc.data["game_state"]["money"] == "6"


def test_load_corrupt_raises(save_dir):
    path = save_dir / "savegame.save"
    path.write_bytes(b"GDEC" + b"\0" * 60)
    with pytest.raises(store.StoreError):
        store.load(path, 0)


def test_profile_values(save_dir):
    data = store.load(save_dir / "savegame.save", 0).data
    assert store.profile_values(data) == {"money": "6", "phase": 1, "products": 113.0}
    assert store.profile_values({}) == {}


def test_write_backup_verify_and_profile(save_dir, tmp_path):
    save_path = save_dir / "savegame.save"
    original = save_path.read_bytes()
    doc = store.load(save_path, 0)
    doc.data["game_state"]["money"] = "6000"
    doc.data["phase"] = 2

    result = store.write(doc, tmp_path / "backups", game_running=lambda: False)

    assert result.warning is None
    assert (result.backup_dir / "savegame.save").read_bytes() == original
    assert (result.backup_dir / "profile.cfg").exists()
    assert not (save_dir / "savegame.save.tmp").exists()
    assert store.load(save_path, 0).data == doc.data
    summary = profile.read_slots((save_dir / "profile.cfg").read_bytes().decode("utf-8"))[0]
    assert summary["money"] == "6000" and summary["phase"] == 2


def test_write_unchanged_data_keeps_same_json(save_dir, tmp_path):
    save_path = save_dir / "savegame.save"
    before = json.loads(crypto.decrypt(save_path.read_bytes()))
    store.write(store.load(save_path, 0), tmp_path / "backups", game_running=lambda: False)
    assert json.loads(crypto.decrypt(save_path.read_bytes())) == before


def test_write_refused_when_game_running(save_dir, tmp_path):
    save_path = save_dir / "savegame.save"
    original = save_path.read_bytes()
    doc = store.load(save_path, 0)
    doc.data["game_state"]["money"] = "1"
    with pytest.raises(store.StoreError):
        store.write(doc, tmp_path / "backups", game_running=lambda: True)
    assert save_path.read_bytes() == original
    assert not (tmp_path / "backups").exists()


def test_write_warns_when_profile_slot_missing(save_dir, tmp_path):
    (save_dir / "profile.cfg").write_bytes(b"[progress]\n\ngame_completed=true\n")
    doc = store.load(save_dir / "savegame.save", 0)
    result = store.write(doc, tmp_path / "backups", game_running=lambda: False)
    assert "profile.cfg" in result.warning


def test_is_game_running_parses_tasklist(monkeypatch):
    found = "\r\nprojectpitt.exe   23244 Console   1   812 345 K\r\n"
    monkeypatch.setattr(store.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=found))
    assert store.is_game_running() is True
    missing = "INFO: No tasks are running which match the specified criteria.\r\n"
    monkeypatch.setattr(store.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=missing))
    assert store.is_game_running() is False
