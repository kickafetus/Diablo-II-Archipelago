# Diablo II Archipelago — Beta 1.9.11

The biggest single-cycle bug-fix release since 1.9.10. This patch closes
18 distinct bugs reported by the Discord community (Congree, Maegis,
Alphena, LXXIX, Saintmillion, Marshe Valias, Koivuklapi, People,
Dank_Santa, Teddie) plus three "supposedly fixed" entries from the
project's Severity Tracker that we re-verified and confirmed already
landed.

---

## Install / update

If you already have a 1.9.10 install: launch the launcher, click
**Update Launcher** when prompted, then **Update Game**. The
self-contained launcher (1.5.x+) handles the full update flow.

If installing fresh: grab `launcher_package.zip`, extract
`Diablo II Archipelago.exe` anywhere, run it — it pulls everything
else automatically.

No more CD-key dialog on fresh install (was scaring newcomers off; this
mod has been offline-only for many releases).

---

## What 1.9.11 fixes

### Critical

- **Skill loss on game crash is REALLY fixed this time.** Congree reported
  losing all skill points after a Hell Ancients crash, even after 1.9.10
  claimed to fix it. Root cause was different: vanilla D2's non-atomic
  `.d2s` write could truncate the skill section mid-write, leaving
  skill bytes at zero on next load. The 1.9.10 fix made *our sidecars*
  atomic but didn't cover D2's own file. The 1.9.11 fix uses the
  per-button cache (atomic since 1.9.10) as a CRASH RECOVERY source —
  the higher of `.d2s` byte vs cache wins. Your character now keeps
  every skill point that was successfully written to *either* file.

- **Apworld sphere logic for skill-hunt mode.** Pre-1.9.11 the
  `skill_hunt` (zone_locking=off) branch collapsed all difficulties
  into one act region per act. Hell Den of Evil and Normal Den of Evil
  lived in the same region — reachable from menu with zero gating. AP
  fill would happily place progression items at Hell-only checks in
  sphere 1, breaking multiworld pacing and creating "you need to be
  in Hell to find the key that unlocks Hell" loops. Now per-difficulty
  act regions chain Menu → Act 1 N → Act 2 N → ... → Act 5 N → Act 1 NM
  (gated on Normal Baal) → ... → Act 5 Hell.

- **Duplicate-gifting on game launch.** Maegis reported receiving 13
  skills + a random charm + a unique+set on game restart with no
  check earned. Root cause: random-drop filler items (charm/set/unique
  apIds 45519-45521) had no across-session dedup — the bridge would
  re-emit them on every connect, and the DLL's 5-second window dedup
  only caught intra-session duplicates. Now we maintain a per-character
  `d2arch_filler_locs_<char>.dat` persistent set keyed by location_id.
  Each unique reward location delivers exactly one drop, ever, no
  matter how many times you restart.

### High

- **CD-key dialog removed.** Patch notes 1.7.0 said this was done; it
  wasn't actually committed. Now it is. New installs go straight to
  download, no dialog scare.

- **AP-connect race window closed.** If you clicked AP Connect then
  Single Player → Character within ~200ms (before the bridge
  authenticated), the character loaded as offline and stayed that way.
  Now `OnCharacterLoad` waits up to 5 seconds for the bridge to
  authenticate before committing to the AP-vs-offline decision.

- **Skill apId no longer permanently eaten if not in pool.** Pre-1.9.11
  if you received a skill item whose ID wasn't in your local skill pool
  (cross-class skill, pool refresh changed, etc.), the apId was marked
  "applied" anyway — the skill was lost forever. Now skills not in the
  pool defer cleanly; if the pool later grows to include the skill,
  the next poll will pick it up.

- **Apworld stops shipping NATIVE-ONLY skills to wrong classes.** In
  custom class-filter mode (`skill_class_filter=1`), the apworld now
  filters out Amazon javelins, Paladin Smite, Barbarian sequences,
  Druid bites, and Assassin kicks/claws when their owning class is
  disabled. Saves multiworld bandwidth and avoids deferred-skill
  notifications for skills the player can never use.

- **Cross-class skill animation cluster (9 sub-bugs in one fix).**
  Severity Tracker had nine "Not Fixed" animation reports from Maegis
  going back to 1.9.2: Barbarian Jump Attack softlock, Whirlwind softlock,
  Double Swing/Throw using casting animation, Paladin Smite casting,
  Assassin Bladefury can't hold to fire, Dragon Claw doesn't hit twice,
  Amazon javelin throws casting, Druid Rabies/Hunger casting. Root cause:
  `RestoreNativeAnimsForClass` early-returned when the boot patch hadn't
  run yet (race with character load), leaving the entire skill table
  stuck in the safe-for-any-class A1 fallback. Now drives the boot
  patch synchronously on first character load if needed.

- **Boss treasure-class fallback values corrected.** 4 of 5 act-boss
  TC IDs were off by 2 (header-row confusion). Duriel was wildly wrong
  at 826 (expected 675). In practice the runtime name lookup masked
  this — fallbacks rarely fired — but now they're correct if a future
  mod or D2 patch shifts the offsets.

- **Per-location filler dedup added to slot-change wipe.** When you
  switch AP slots, the new `d2arch_filler_locs_<char>.dat` from 1.9.11
  also gets cleared so the new slot's location IDs aren't suppressed.

### Medium

- **Boss shuffle no longer copies AI.** People + Maegis reported
  "invincible / invisible boss" and wrong death cinematics. Cause: each
  act boss's AI is tied to spawn-marker, hitbox, and death-cinematic
  trigger specific to that boss's location. Swapping AI made bosses
  walk to non-existent spawns or play the wrong cinematic. Boss shuffle
  now keeps each slot's native AI; only cosmetic (sprite, name, sound)
  + drop tables get swapped. You'll still see "Andariel" looking like
  Mephisto — the visual variety stays, the function works.

- **Monster shuffle skips swaps with empty name strings.** Defense
  against Maegis's "champion enemies no names" — some replacement
  monsters in the preset pool have `nameStr=0` and would propagate
  the no-name into champion lookups. Now those swaps are skipped.

- **Waypoint check no longer races zone teleport.** When entrance
  shuffle warps you, the area ID briefly reads as the source zone
  before D2 updates it. Pre-1.9.11 a waypoint scan in this window
  could double-fire or miss the check. Now we skip the scan entirely
  while a teleport is pending.

- **ESC closes both our panels and D2's panels in one press.** Alphena
  reported ESC closing stash but leaving the skill tree stuck (or vice
  versa). Pre-1.9.11 we ate ESC after closing our panel — D2 never
  saw it. Now ESC closes everything in one press. Lesser evil than
  half-open states requiring alt-tab to recover.

- **Chest cheat closed.** LXXIX reported spamming a locked chest with
  no key still progressing chest checks. Now we only fire the chest
  check + counter if D2 actually opened the chest (operation mode
  advanced after the trampoline call).

- **Launcher "Repair Files" no longer overwrites your `d2gl.ini`.**
  Maegis 1.9.2: "Most video settings get changed back to default
  preventing player from playing in Fullscreen from launch." Added
  `USER_EDITABLE_FILES` skip list — `d2gl.ini`, `D2Hackmap.ini`,
  `d2sigma.ini`, `d2gl_userkeys.ini`, `keymap.ini` are now present-is-
  valid; Repair fills them if missing but never overwrites a present
  file.

### Low

- **Launcher self-update writes version file only on xcopy success.**
  Pre-1.9.11 the version file was written BEFORE xcopy, so a failed
  copy (AV holding the .exe, disk full) left the launcher claiming
  to be updated when the binary was still the old version. Now the
  bat checks errorlevel and only stamps the version on success. Logs
  to `launcher_update.log` so you can see what happened.

- **Bridge log no longer spams "Found state file" every tick.**
  Koivuklapi reported MBs/hour of identical log lines. Now one-shot
  per file.

---

## Verified already-fixed (Severity Tracker entries cleared)

- **B29 — Stash item destroy on tab click**: fixed in 1.9.5 commit
  `dfbd532`. Tracker entry stale.
- **B31 — Holy Bolt pierces + damages demons**: fixed in 1.9.1 commit
  `bc8ed87`. Tracker entry stale.
- **B32 — Random objects in shared stash on new char**: 1.9.0-era dev
  artifact; `shared_stash.dat` has been excluded from `game_package.zip`
  since the `_pack_game.py` SKIP list landed. Tracker entry stale.

---

## Known issues — still under investigation

These need user-side diagnostics before we can fix in 1.9.12:

- **Failed to inject error 87/5** (Saintmillion) — typically AV
  blocking. We'll add an explicit "add Game.exe + launcher to AV
  exceptions" diagnostic dialog in 1.9.12.
- **Random unique amulet/charm spawns as magical** (Maegis) — needs
  Ghidra trace of D2's QUESTS_CreateItem to understand the silent
  downgrade for certain unique types.
- **Treasure cow prompt is very large** (Maegis) — need screenshot
  to identify which dialog (multiple cow-related UI elements exist).
- **Sacrifice doesn't drain HP** (Maegis 1.9.0 — confirmed still
  present) — needs Ghidra to find the right D2 hook point.
- **"An Evil Force" text for lightning resist/damage** (Marshe Valias) —
  need debug-log capture of the failing string key lookup so we don't
  blind-write entries that might collide with existing keys.
- **Skill page no info display** (Maegis) — re-test after 1.9.11 anim
  cluster fix; likely resolved.

The following should re-test as resolved after 1.9.11 lands:

- **Act 3 crash** (Teddie) — B1 + B7 fixes plausibly cover this.
- **Pit→Tower L2 stairs** (Maegis) — likely covered by the 1.9.5
  Forgotten Tower fix.
- **TP-during-ES auto-fails Cain** (Maegis) — likely covered by 1.9.10
  Cain state 14/15 filter.

If any of the above are still broken after testing 1.9.11, please
re-post on Discord with a screenshot or `d2arch.log` excerpt.

---

## Deferred to 1.9.12+

- **Entrance Shuffle WP landing** (Maegis #6) — 4-6 hour Ghidra-heavy
  warp-tile coord scan. Quality-of-life only, not a softlock.
- **ItemLevelReqs toggle for vanilla loot** (Maegis #2 second half) —
  needs design decision: strip stats 91/92/93 on all item pickups
  (monster drops, shop, gambling) vs AP-delivered only.

---

## Build artifacts

| Artifact | Size | Notes |
|---|---|---|
| `Game/D2Archipelago.dll` | ~712 KB | "Beta 1.9.11" embedded |
| `Game/D2Arch_Launcher.exe` | ~120 KB | "Beta 1.9.11" baked in |
| `Game/ap_bridge_dist/ap_bridge.exe` | ~2.9 MB | PyInstaller Python 3.13 |
| `Game/apworld/diablo2_archipelago.apworld` | ~55 KB | `world_version: 1.9.11` |
| `launcher_package.zip` | ~68 MB | Self-contained 1.5.5 |

*Cycle started 2026-05-19 on top of Beta 1.9.10 baseline. Released 2026-05-22.*
