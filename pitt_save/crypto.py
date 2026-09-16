"""Godot 4 FileAccessEncrypted format (FileAccess.open_encrypted_with_pass)."""
import hashlib
import os
import struct

from Crypto.Cipher import AES

PASSWORD = "I_SEE_YOU_BUT_YOU_SHOULD_NOT_SEE_THAT"
MAGIC = b"GDEC"
HEADER_SIZE = 44  # magic(4) + md5(16) + length(8) + iv(16)


class SaveFormatError(ValueError):
    """Unreadable file: unknown format, truncated, or wrong key."""


def _cipher(password: str, iv: bytes):
    # Godot uses the 32 hex characters of md5(password) as the AES-256 key.
    key = hashlib.md5(password.encode("utf-8")).hexdigest().encode("ascii")
    return AES.new(key, AES.MODE_CFB, iv=iv, segment_size=128)


def decrypt(blob: bytes, password: str = PASSWORD) -> bytes:
    if blob[:1] == b"{":  # the game also accepts a plain JSON save
        return blob
    if len(blob) < HEADER_SIZE or blob[:4] != MAGIC:
        raise SaveFormatError("No GDEC header: this is not an encrypted Godot save.")
    md5 = blob[4:20]
    (length,) = struct.unpack_from("<Q", blob, 20)
    iv = blob[28:44]
    padded = (length + 15) // 16 * 16
    if len(blob) < HEADER_SIZE + padded:
        raise SaveFormatError("Truncated file.")
    plain = _cipher(password, iv).decrypt(blob[HEADER_SIZE:HEADER_SIZE + padded])[:length]
    if hashlib.md5(plain).digest() != md5:
        raise SaveFormatError("MD5 mismatch: wrong key or corrupt file.")
    return plain


def encrypt(plain: bytes, password: str = PASSWORD, iv: bytes | None = None) -> bytes:
    iv = os.urandom(16) if iv is None else iv
    padded = plain + b"\0" * (-len(plain) % 16)
    body = _cipher(password, iv).encrypt(padded)
    return MAGIC + hashlib.md5(plain).digest() + struct.pack("<Q", len(plain)) + iv + body
