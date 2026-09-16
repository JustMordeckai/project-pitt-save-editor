# Project P.I.T.T save format

Notes gathered while building the editor, for build `1.0.5` (Godot 4.7.2). Everything here comes
from the shipped game files.

## Files

`%APPDATA%\Godot\app_userdata\Project P.I.T.T\`

| File | Contents |
|---|---|
| `savegame.save` | Slot 0. Other slots are `savegame_N.save` (10 slots max). |
| `savegame.save.bak` | Previous save, written by the game. |
| `savegame.save.corrupt` | Quarantined save: the game wrote this when it could not parse one. |
| `profile.cfg` | Godot `ConfigFile`: `[slots]` with `last_slot` and a `slot_N={...}` summary (`money`, `name`, `phase`, `play_time`, `products`, `timestamp`), plus `[progress]` for the endings. |
| `settings.cfg`, `graphics_settings.cfg`, `locale.cfg` | Options, plain `ConfigFile`. |

Steam Auto-Cloud is enabled for this folder.

## Encryption

`savegame.save` is written with `FileAccess.open_encrypted_with_pass`. The password is the
`SAVE_PASSWORD` constant in `scripts/save_manager.gdc`:

```
I_SEE_YOU_BUT_YOU_SHOULD_NOT_SEE_THAT
```

Layout:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | magic `GDEC` |
| 4 | 16 | MD5 of the plaintext |
| 20 | 8 | plaintext length, `uint64` little-endian |
| 28 | 16 | IV |
| 44 | length rounded up to a multiple of 16 | ciphertext, zero-padded |

The cipher is AES-256-CFB with a 128-bit segment size. The key is not the password itself: Godot
takes `md5(password)` as a 32-character hex string and uses those 32 ASCII bytes as the key.
Decrypting yields compact UTF-8 JSON, and the MD5 in the header verifies it.

`SaveManager._read_save_string` also accepts a plaintext save: if the file starts with `{`, it is
parsed as JSON directly.

## Save contents

Top-level keys: `version`, `timestamp`, `phase`, `game_state`, `game_statistics`, `object_pools`,
`unlocked_milestones`, `seen_items`, `minable_blocks`, `cameras`, `fuses`, `hole`, `vertical_gates`,
`workbenches`, `loop_puzzle`, `pickaxe`, `music`, `player_position`, and a few spawn flags.

Things worth knowing before editing:

- **Money is a string.** `money`, `total_money_gained`, `total_money_spent`, `combo_bonus_total` and
  `total_bonus_earned` are decimal strings parsed by the game's `BigInt` class. Write `"6000"`, not `6000`.
- **`phase`** is 0 to 4; a saved `5` is clamped back to 4 on load.
- **Upgrade categories** (`upgrades`, `tools`, `toys`, `combos`) are `{name: {"enabled": bool, "level": int}}`.
  `products` nest one level deeper: `{name: {"enabled": bool, "craft_speed": {"level": int}, ...}}`.
- **`unlocked_milestones`** is the list of unlock events that already fired. Adding an id marks the
  event as done rather than granting the item; the item itself lives in the category above.
- **`profile.cfg` mirrors the save**: `money`, `phase` and `products` are copied into `slot_N`, so a
  save edited without updating it shows stale values in the game's slot picker.
- Godot's JSON parser accepts exponent notation, so re-serializing floats from another language
  (`-4.3e-05` instead of `-0.000043`) loads fine, verified in game.

## Reading the game's scripts

`projectpitt.pck` is a standard Godot pack: magic `GDPC`, pack format 4, engine 4.7.2, flags `2`
(relative file base, directory **not** encrypted), so the file table can be read directly.

Scripts are exported as binary tokens, not source: each `.gdc` starts with `GDSC`, a version
(`101` here) and the decompressed size, followed by a zstd frame. The decompressed buffer starts
with four `uint32` counts (identifiers, constants, token lines, tokens), then the identifier table
(each identifier is a length followed by UTF-32 code points, every byte XORed with `0xB6`), then the
constants as encoded `Variant`s. Reading just the identifiers and string constants is enough to find
things like the save password or the milestone list, without rebuilding the token stream.
