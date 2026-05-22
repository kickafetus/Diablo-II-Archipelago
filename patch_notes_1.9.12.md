# Diablo II Archipelago — Beta 1.9.12

A small follow-up release to 1.9.11 that closes the three bugs we could
fix without needing more diagnostic information from users. Plus one
new opt-in feature: making any item equippable regardless of
level/STR/DEX (extends what AP-delivered items already do to vanilla
loot).

---

## Install / update

Existing 1.9.11 install: launch the launcher, click **Update Launcher**
when prompted, then **Update Game**.

Fresh install: grab `launcher_package.zip`, extract
`Diablo II Archipelago.exe` anywhere, run it — pulls everything else
automatically. No CD-key dialog. No .NET runtime needed.

---

## What 1.9.12 fixes

### B33 — "An Evil Force" lightning resistance / damage text

Marshe Valias reported that enemy lightning resistance tooltips and
Lightning skill damage tooltips both displayed "An Evil Force" instead
of the proper text. Root cause: 8 missing modifier-string keys in
`patchstring.tbl`. D2 looked them up, found nothing, and fell back to
the placeholder string used for unmapped keys.

Added 8 keys to `patchstring.tbl` covering all three elemental
resistances + lightning damage min/max + the max-resist trio:

- `ModStr1j` = `Fire Resist`
- `ModStr1k` = `Cold Resist`
- `ModStr1l` = `Lightning Resist`
- `ModStr1q` = `to Maximum Lightning Damage`
- `ModStr1r` = `to Minimum Lightning Damage`
- `ModStr5u` = `to Maximum Fire Resist`
- `ModStr5v` = `to Maximum Cold Resist`
- `ModStr5w` = `to Maximum Lightning Resist`

(We added all three elements because they were all missing — a free
fix for fire and cold tooltips too.)

### B18 — "Failed to inject error 87/5" launcher diagnostics

Saintmillion reported that the game wouldn't launch — `D2Arch_Launcher`
exited with the cryptic message "Failed to inject (error 87)" (or
error 5) and no clue what to do about it. The bootstrap had minimal
error reporting and no retry logic.

Improvements in `D2Arch_Launcher.exe`:

- **Per-step error messages** — when injection fails you now see WHICH
  Windows call failed (OpenProcess / VirtualAllocEx / WriteProcessMemory
  / CreateRemoteThread) plus a human-readable hint for the most common
  causes per error code.
- **Stale Game.exe cleanup** — kills any leftover Game.exe from a
  previous failed launch before starting a fresh one (this was the
  #2 root cause).
- **Retry with backoff** — 3 attempts spaced 500ms apart; transient
  failures (AV scanning the DLL, target process not yet stable) no
  longer kill the launch.
- **WriteProcessMemory return-value check** — previously ignored, so
  a silently-failed write would cascade into a garbage LoadLibrary
  call.
- **Antivirus exception guidance** — for the most common case (error
  5/87 = AV blocking), the error message now explicitly tells you to
  add `Game.exe` + `D2Arch_Launcher.exe` to your AV exception list,
  with step-by-step instructions for Windows Defender.

If injection still fails after these improvements, you'll get a much
clearer error to copy-paste into Discord.

### ItemLevelReqs toggle for vanilla loot (Maegis #2 second half)

The AP-delivered side has stripped level/STR/DEX equip requirements
from delivered items since 1.9.4 — but vanilla monster drops, shop
items, and gambling still enforced them. Maegis asked for parity.

New `d2arch.ini` setting under `[settings]`:

```ini
ItemLevelReqs=1   ; default — vanilla equip requirements apply (current behavior)
ItemLevelReqs=0   ; new — strip level/STR/DEX from ALL items, any character can equip anything
```

The setting is OPT-IN (default on = keep vanilla behavior) so users
who want the difficulty progression are unaffected. Toggle to 0 and
your level-1 character can wear that level-65 unique you found.

---

## Verified-fixed in 1.9.11 — Tracker entries cleared

Three bugs that were marked "Not Fixed" in the project's Severity
Tracker turned out to already be addressed in earlier releases:

- **B29 — Stash item destroy on tab click** (fixed in 1.9.5 commit
  `dfbd532`)
- **B31 — Holy Bolt pierce + damages demons** (fixed in 1.9.1 commit
  `bc8ed87`)
- **B32 — Random objects in shared stash on new char** (excluded from
  game package via `_pack_game.py` SKIP list — was dev-only artifact)

If you were holding off on these because of the tracker entries, they
should already be working as of 1.9.11. Re-test if curious.

---

## Known issues — still under investigation

These bugs need user-side diagnostic data before we can fix in 1.9.13.
If you can reproduce any of them, please share the requested info on
Discord.

### Likely already fixed by 1.9.10/1.9.11 — please re-test

- **Act 3 crash** (Teddie) — 1.9.10 atomic-write + 1.9.11 B1 (real
  skill-loss fix) + B7 (AP-connect race close) plausibly cover this.
- **TP location reset** (Alphena) — 1.9.11 B1 + B4 (slot-change wipe
  extend) plausibly cover this.
- **Pit→Tower L2 stairs** (Maegis 1.9.0) — the 1.9.5 Forgotten Tower
  fix at `d2arch_levelshuffle.c:102` was for this exact symptom.
- **TP-during-ES auto-fails Cain** (Maegis) — 1.9.10 Cain state
  14/15 filter explicitly handles this case.
- **Skill page no info** (Maegis) — likely the 1.9.11 B5+B28 cross-
  class anim cluster fix.
- **Champion enemies no names** (Maegis) — likely the 1.9.11 B14
  monster shuffle `nameStr=0` defense.
- **Sacrifice doesn't drain HP** (Maegis 1.9.0) — verified `Skills.txt`
  has the correct `param3=8` (vanilla HP cost), `srvdofunc=64`
  unchanged, anim outside our patch range. Our boot patches don't
  touch the HP cost path. If still broken in 1.9.12, root cause is
  in D2Game internal `srvdofunc 64` behavior — requires Ghidra hook.

### Need specific data

- **Random unique amulet/charm spawns magical** (Maegis) — if you can
  reproduce in 1.9.12, please log the apId received + the resulting
  item code + char level via `Game/Archipelago/d2arch.log`.
- **Failed to inject error 87/5** (Saintmillion) — please re-test with
  1.9.12 — the new diagnostics should explain WHY. If AV exception
  doesn't help, share the exact error output.
- **Treasure cow prompt is very large** (Maegis) — please post a
  screenshot of the oversized dialog so we know WHICH cow-related UI
  to fix.

---

## Deferred to 1.9.13+

- **Entrance Shuffle WP landing** (Maegis #6) — needs in-game testing
  to identify the right D2 ord for safe post-warp coord-set. The
  manual room scan + ord 10027 approach crashed in 2026-04-27 testing.
  Quality-of-life only (lands on WP instead of cave-mouth, no
  softlock). 4-6 hour Ghidra+test cycle needed.
- **Sphere-depth assertion in validation harness** — needs full
  Archipelago framework source set up locally. The 1.9.11 B9 fix is
  statically verified — no regression risk for 1.9.12.

---

## Build artifacts

| Artifact | Size | Notes |
|---|---|---|
| `Game/D2Archipelago.dll` | ~713 KB | "Beta 1.9.12" embedded |
| `Game/D2Arch_Launcher.exe` | ~125 KB | "Beta 1.9.12" + B18 fixes |
| `Game/ap_bridge_dist/ap_bridge.exe` | ~2.9 MB | PyInstaller Python 3.13 |
| `Game/apworld/diablo2_archipelago.apworld` | 56,524 bytes | `world_version: 1.9.12` |
| `launcher_package.zip` | ~68 MB | Self-contained 1.5.6 |

*Cycle started + released 2026-05-22 on top of Beta 1.9.11 baseline.*
