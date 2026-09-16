import pytest

from pitt_save import profile

PROFILE = """[slots]

last_slot=0
slot_0={
"money": "6",
"name": "",
"phase": 1,
"play_time": 720.0204153333347,
"products": 113.0,
"timestamp": 1789508534.536
}
slot_1={
"money": "42",
"name": "",
"phase": 3,
"play_time": 1.0,
"products": 2.0,
"timestamp": 1.0
}

[progress]

game_completed=true
"""


def test_read_slots():
    slots = profile.read_slots(PROFILE)
    assert sorted(slots) == [0, 1]
    assert slots[0] == {
        "money": "6", "name": "", "phase": 1, "play_time": 720.0204153333347,
        "products": 113.0, "timestamp": 1789508534.536,
    }
    assert slots[1]["money"] == "42"


def test_read_slots_empty_file():
    assert profile.read_slots("") == {}


def test_patch_only_targeted_slot_and_values():
    out = profile.patch_slot(PROFILE, 0, {"money": "6000", "phase": 3, "products": 150.0})
    slots = profile.read_slots(out)
    assert slots[0]["money"] == "6000" and slots[0]["phase"] == 3 and slots[0]["products"] == 150.0
    assert slots[1] == profile.read_slots(PROFILE)[1]
    expected = (PROFILE.replace('"money": "6",', '"money": "6000",', 1)
                .replace('"phase": 1,', '"phase": 3,', 1)
                .replace('"products": 113.0,', '"products": 150.0,', 1))
    assert out == expected


def test_patch_last_key_keeps_no_comma():
    out = profile.patch_slot(PROFILE, 0, {"timestamp": 1.5})
    assert '"timestamp": 1.5\n}' in out


def test_patch_preserves_crlf():
    crlf = PROFILE.replace("\n", "\r\n")
    out = profile.patch_slot(crlf, 1, {"money": "7"})
    assert out == crlf.replace('"money": "42",', '"money": "7",')


def test_patch_missing_slot_raises():
    with pytest.raises(profile.ProfileError):
        profile.patch_slot(PROFILE, 5, {"money": "1"})


def test_patch_missing_key_raises():
    with pytest.raises(profile.ProfileError):
        profile.patch_slot(PROFILE, 0, {"unknown": 1})
