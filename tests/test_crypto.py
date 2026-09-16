import json
from pathlib import Path

import pytest

from pitt_save import crypto

FIXTURE = Path(__file__).parent / "fixtures" / "savegame.save"


def test_decrypt_real_save_gives_json():
    data = json.loads(crypto.decrypt(FIXTURE.read_bytes()))
    assert data["version"] == "1.0.5"
    assert data["game_state"]["money"] == "6"


def test_reencrypt_with_same_iv_is_byte_identical():
    blob = FIXTURE.read_bytes()
    assert crypto.encrypt(crypto.decrypt(blob), iv=blob[28:44]) == blob


def test_encrypt_with_random_iv_roundtrips():
    plain = b'{"a":1}'
    blob = crypto.encrypt(plain)
    assert blob[:4] == b"GDEC"
    assert crypto.decrypt(blob) == plain


def test_block_aligned_length_roundtrips():
    plain = b"x" * 32
    assert crypto.decrypt(crypto.encrypt(plain)) == plain


def test_wrong_password_rejected():
    with pytest.raises(crypto.SaveFormatError):
        crypto.decrypt(FIXTURE.read_bytes(), password="wrong")


def test_plain_json_is_accepted_as_is():
    assert crypto.decrypt(b'{"x":2}') == b'{"x":2}'


def test_unknown_format_rejected():
    with pytest.raises(crypto.SaveFormatError):
        crypto.decrypt(b"this is definitely not a Godot save file............")


def test_truncated_file_rejected():
    with pytest.raises(crypto.SaveFormatError):
        crypto.decrypt(FIXTURE.read_bytes()[:100])
